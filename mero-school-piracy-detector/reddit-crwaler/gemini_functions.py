import os
import pathlib
import textwrap

import google.generativeai as genai
from PIL import Image as PILImage
from dotenv import load_dotenv
load_dotenv()

# from IPython.display import display
# from IPython.display import Markdown


# def to_markdown(text):
#   text = text.replace('•', '  *')
#   return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))
class GeminiResponse:
    def __init__(self, history=None):
      if history:
        self.history=history
      else:
        self.history = []

      self.genai = genai
      self.genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

      # Set up the model
      self.generation_config = {
        "temperature": 0.9, # low temperature gives better results for new posts
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
      }
      
      self.safety_settings = [
        {
          "category": "HARM_CATEGORY_HARASSMENT",
          "threshold": 'BLOCK_NONE',               # "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
          "category": "HARM_CATEGORY_HATE_SPEECH",
          "threshold": 'BLOCK_NONE',               # "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
          "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
          "threshold": 'BLOCK_NONE',               # "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
          "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
          "threshold": 'BLOCK_NONE',               # "BLOCK_MEDIUM_AND_ABOVE"
        }
      ]
      self.ai4growth_history = [
              {
                  "role": "user",
                  "parts": ["imagine you are an AI researcher at NAAMII Institute. NAAMII stands for NepAl Applied Mathematics and Informatics Institute. it is an institute in nepal. you are researching on implementing AGI. your name is \"Genna GenAi\". you are answering queries of users in a discord channel called \"AI4GROWTH\". AI4GROWTH is the result of partnership of \"NAAMII\" and \"Kings college\". AI4GROWTH offers AI courses. .please answer questions i will ask subsequently. Also please do not introduce yourself unless someone explicitly asks you to do so."]
              }
              ,
              {
                  "role": "model",
                  "parts": ["ok."]
              }
          ]
      self.text_model = genai.GenerativeModel(model_name="gemini-1.0-pro-001",      # "gemini-1.0-pro",
                                  generation_config=self.generation_config,
                                  safety_settings=self.safety_settings)
      self.convo = self.text_model.start_chat(history=history)

      self.vision_model = genai.GenerativeModel('gemini-pro-vision')
    def get_gemini_response(self, prompt, image_path=None, history=None, temperature = 0.9):
        self.generation_config['temperature'] = temperature # low temperature gives better results for new posts
        if not image_path:
            # pure text as input
            # ---------------
            
            
            try:
              self.convo.send_message(prompt)
            except Exception as Ex:
              print(Ex)
              try:
                self.convo.send_message(prompt)
              except Exception as Ex2:
                return '', []
            model_response = self.convo.last.text
            
        else:
            # Image as input
            # ---------------
            
            img = PILImage.open(image_path)
            response = self.vision_model.generate_content([prompt, img], stream=True)
            response.resolve()
            model_response = response.text
            # print(response.text)
            # return model_response, history
        if history:
              history.extend([
                {"role": "user", "parts": [prompt]},
                {"role": "model", "parts": [model_response]}
                ])
        else:
          history = [
            {"role": "user", "parts": [prompt]},
            {"role": "model", "parts": [model_response]}
            ]
        return model_response, history
# -----------------------------------
# ///////Gemini Response//////////////
# -----------------------------------


if __name__ == "__main__":
    gemi = GeminiResponse()
    response_text, the_history = gemi.get_gemini_response(image_path = 'images/image.jpeg', prompt="Describe what you see.")
    print(f'response_text:{response_text}, \n\n history:{the_history} \n\n')
    

    history_new = [
            {
                "role": "user",
                # Your mastodon username is 'aananda' and your display name is: 'kritrim'. 'kritrim' means 'artificial' in sanskrit. you are about to complete bachelors degree in 'Electronics and Communication Engineering'.
                "parts": ["Imagine you are mastadon user. You are interested in making artificial general intelligence. your display name is: 'kritrim'. 'kritrim' means 'artificial' in sanskrit. Please do not give away your personal information unless someone explicitly asked about it. I repeat, do not give away your personal information."]
            },
            {
                "role": "model",
                "parts": ["ok."]
            }
        ]
    gemi = GeminiResponse(history=history_new)
    mastodon_post_content = """ACW 2.0: September, Show 2, Year 4</p><p><a href="https://acwontnm.blogspot.com/2024/03/september-show-2-year-4.html" rel="nofollow noopener noreferrer" translate="no" target="_blank"><span class="invisible">https://</span><span class="ellipsis">acwontnm.blogspot.com/2024/03/</span><span class="invisible">september-show-2-year-4.html</span></a></p><p><a href="https://mastodon.online/tags/TNM7" class="mention hashtag" rel="nofollow noopener noreferrer" target="_blank">#<span>TNM7</span></a></p>"""
    the_gemini_response, history = gemi.get_gemini_response(prompt="please write a suitable comment for this post. Imagine you are directly commenting in this users post. and please keep the comment informal and short if possible. comment should not sould like it was generated by a llm. You are not generative ai. you are human. below is the post: " + mastodon_post_content, history=history_new)# "Hi! how you doing?")
    # the_gemini_response = get_gemini_response(prompt="can you please list the names of repositories in this github  account: https://github.com/aananda-giri/.", history=None)# "Hi! how you doing?")
    print(f'\n\nresponse_text:{the_gemini_response}, \n\n history:{history} \n\n')
