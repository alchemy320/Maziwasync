import json
import os

from groq import Groq
import joblib
from dotenv import load_dotenv

class CattleAIService:
    def __init__(self):
        # constructor that will load the ML files and will initialize the Groq Ai engine
        base_dir=os.path.dirname(os.path.abspath(__file__))
        # read keys inside local .env config file into memory
        load_dotenv()
        self.model=joblib.load(os.path.join(base_dir, 'cattle_disease_model.pkl'))

        # loading the features/x/inputs
        self.model_features=joblib.load(os.path.join(base_dir, 'model_features.pkl'))

        # extract the symptoms from the model_features
        self.valid_symptoms=[
            f for f in self.model_features
            if f not in ['Age', 'Temperature'] and not f.startswith('animal')
        ]

        # setup and authenticate the Groq cloud connection
        self.groq_client=Groq(api_key=os.environ.get('GROQ_API_KEY'))

    # method to extract the farmer conservation and structure symptoms
    def extract_symptoms_with_groq(self,farmer_text):
            # comand groq and force it to response strictly with valid symptoms in json format
            system_prompt=f"""
            You are a vetenary assistant. Analyse the text and extract symptoms matching exactly this list
            {self.valid_symptoms}
            Respond with a JSON object:{{"symptoms:[system_name"]}}
            """

            try:
                Completion=self.groq_client.chat.completions.create(
                    messages=[
                        {"role":"system", "content":system_prompt},
                        {"role":"user", "content":f"Farmer text:\"{farmer_text}\""}
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.0,
                    response_format={"type":"json_object"}
                )
                response_text=Completion.choices[0].message.content.strip()
                result_json=json.loads(response_text)
                return result_json.get('symptoms',[])

            except Exception as e:
                print(f"Groq Extraction Error: {e}")
                return []
            
    def get_treatment_recomendation(self, disease, animal_type):
        # query the Groq LLM to generate instant medical advice and emergency instruction
        system_prompt=("""
        You are an expert livestock veteranian, provide clear, concise and proffesional treatment recomendations under 120 words using short bullets points. include a vet disclaimer
        """)

        try:
            Completion=self.groq_client.chat.completions.create(
                messages=[
                    {"role":"system", "content":system_prompt},
                    {"role":"user", "content":f"Treatment recomendation for a {animal_type} with {disease}"}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.3,
            
            )
            return Completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq Treatment Error: {e}")
            return "Treatment temporarily unavailable."

    def predict(self, animal_type, age, temp, description):
        #  use the LLM extraction utility to filter symptoms out of the incoming text string
        extracted_symptoms=self.extract_symptoms_with_groq(description)

        # build baseline dictionary mapping all training features name to zero values
        input_data={feature: 0 for feature in self.model_features}

        # map raw numeric inputs to their respective matching feature keys
        input_data['Age']=age
        input_data['Temperature']=temp
        # convert animal string into one columns key format name string 'Animal_COW
        animal_key=f"Animal_{str(animal_type).strip().lower()}"
        if animal_key in input_data:
            input_data[animal_key]=1

        for symptom in extracted_symptoms:
            if symptom in input_data:
                input_data[symptom]=1

        # flatten the dict into ordered list matching the exact index setup our model
        final_input_vector=[input_data[feature] for feature in self.model_features]
        prediction=self.model.predict([final_input_vector])
        # extract the precition at index
        predicted_disease=prediction[0]

        treatment_plan=self.get_treatment_recomendation(predicted_disease, animal_type)
        # 
        # return consolidated final pipeline patload output directly back to DRF response

        return {
            "status": "success",
            "extracted_symptoms_by_ai": extracted_symptoms,
            "predicted_disease": predicted_disease,
            "treatment_recomendation": treatment_plan
        }
