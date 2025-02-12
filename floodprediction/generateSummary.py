from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch


client = genai.Client(api_key="AIzaSyDhTxISQgZD39bXdFS8OM7kxV7dVbB0WvQ")
model_id = "gemini-2.0-flash-exp"

google_search_tool = Tool(
    google_search = GoogleSearch())

def generate_disaster_summary(disaster_date: str, month_occurred: str, disaster_location: str, disaster_type: str,
                               total_deaths: int, total_injured: int, total_affected: int) -> str:
    ##  Improved prompt
    prompt = f'''
        Generate a **detailed and professional disaster impact report** for a {disaster_type} that occurred on **{disaster_date}** in **{disaster_location}**.  
        
        ### **Guidelines for Generating the Report:**
        - Maintain a **formal and informative** tone suitable for a government report or news article.  
        - Present the details **in a structured manner**, ensuring clarity and readability.  
        - If specific numerical data is provided, highlight its significance and **explain its impact**.  
        - If any information is unavailable, replace it with **contextual insights or estimates** to maintain coherence.  
        - Ensure that the **title is concise yet impactful**, mentioning the disaster type and location.  
        - The report should follow the **structure outlined below**.

        ### **Report Structure & Formatting:**  

        **Title:**  
        Provide a suitable headline summarizing the disaster. Include the disaster type, location, and month of occurrence (e.g., *Cyclone Remal's Devastation in Odisha and West Bengal – May 2024*).  

        **Cause:**  
        Describe the underlying reasons for the disaster, including environmental, meteorological, or human-induced factors. Mention any contributing phenomena like **climate change, tectonic activity, or extreme weather conditions**.  

        **Effects:**  
        Detail the **human, infrastructural, and economic impact** of the disaster. Break down the effects into the following categories:  

        - **Human Impact:**  
          - **Total deaths:** {total_deaths if total_deaths != 'information unavailable' else 'Data unavailable'}  
          - **Total injured:** {total_injured if total_injured != 'information unavailable' else 'Data unavailable'}  
          - **Total affected:** {total_affected if total_affected != 'information unavailable' else 'Data unavailable'}  
          - Describe how communities were affected, including displacement, casualties, and emergency response efforts.  

        - **Infrastructure Damage:**  
          - Explain the extent of destruction to **homes, roads, power lines, communication networks, and critical facilities**.  
          - Mention **disruptions in utilities, transportation, and emergency services**.  

        - **Economic Consequences:**  
          - Assess the **financial toll on local economies**, including damage to **agriculture, businesses, and industries**.  
          - If **economic loss figures are not available**, provide estimates based on similar past events.  

        **Response & Relief Efforts:**  
        Summarize the **immediate and long-term response efforts** by the government, NGOs, and international agencies.  
        - Mention **evacuations, relief aid, medical support, and infrastructure restoration plans**.  
        - Highlight **any notable challenges faced during rescue operations**.  

        **Conclusion & Future Preparedness:**  
        Discuss lessons learned from this disaster and suggest improvements in **disaster preparedness, early warning systems, and policy measures** to mitigate future risks.  

        **Additional Considerations:**  
        - Avoid generic statements—back up claims with **facts, historical comparisons, or expert insights**.  
        - Ensure that the **report reads naturally and flows smoothly**, maintaining a professional tone throughout.  
        - Do not include unnecessary explanations about the format—**start directly with the title and structured content**.

        I want you to fill the missing information like if its not available with proper numbers or terms  
        The numbers provided by me can be misleading so search web for proper answers and numbers
    '''

    response = client.models.generate_content(model=model_id, contents=prompt,
                                              config=GenerateContentConfig(
                                                  tools=[google_search_tool],
                                                  response_modalities=["TEXT"],)
                                             )
    return response.text