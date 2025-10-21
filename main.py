#This is a python File

from google import genai

client = genai.Client(api_key="AIzaSyC3XOsYy-Tqw25cAK_opEZ0435vZQnvKl0")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words",
)

print(response.text)