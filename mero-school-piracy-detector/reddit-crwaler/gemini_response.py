# def gemini_functions(post_title, comment_body):
#     mero_school_varients = ['meroschool', 'mero-school', 'mero school', 'mero_school']
    
#     return True in [varient in post_title.lower() or varient in comment_body.lower() for varient in mero_school_varients]

from dotenv import load_dotenv
from gemini_functions import GeminiResponse

load_dotenv()
gemini = GeminiResponse()

def is_mero_school_related_post(post_content, image_path = None):
    response_text, the_history = gemini.get_gemini_response(image_path = image_path, prompt="This is reddit post. Your job is to classify whether or not this post is related to \"mero-school\". Mero school is educational platform that make videos similar to coursera.  The problem is people download the videos and post the links to downloaded videos in reddit. which is piracy. Give one word respose: \"true\" if this post is related to mero-school and \"false\" if this post is not related to mero-school. note: The post might be in \"nepali\" language or in \"english\" language This is the post content: ```" + post_content+"```", temperature=0.0)
    
    # print(f'response_text:{response_text}')     # , \n\n history:{the_history} \n\n')
    true_varients=['"True"', "'TRUE'", "'True'", 'true', "'true'", '"true"', 'True', '"TRUE"', 'TRUE']
    if True in [true_varient in response_text for true_varient in true_varients]:
        return True
    else:
        return False

if __name__=="__main__":
    # Testing Few links
    post_content="""Mero school ko videos haru bhako jati share garum ta.

    maths I anyone?"""
    post_content="ajo k gari rako chau"


    post_content='''
    Mero school ko videos haru bhako jati share garum ta 

    ma sanga ta chaina
    '''
    print(f'post_content:{post_content}\n\n is_mero_school_related_post:{is_mero_school_related_post(post_content)}')