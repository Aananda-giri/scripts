import os

from dotenv import load_dotenv
import google.generativeai as genai

import pathlib
import textwrap
import time

load_dotenv()

genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')


def is_mero_school_related_post(post_content, temperature=0.0):
    prompt="This is reddit post. Your job is to classify whether or not this post is related to \"mero-school\". Mero school is educational platform that make videos similar to coursera.  The problem is people download the videos and post the links to downloaded videos in reddit. which is piracy. Give one word respose: \"true\" if this post is related to mero-school and \"false\" if this post is not related to mero-school. note: The post might contain \"nepali\" language or in \"english\" language. This is the post content: ```" + post_content+"```"
    try:
        response_text = model.generate_content(prompt).text
        print(f'response_text:{response_text}')     # , \n\n history:{the_history} \n\n')
        true_varients=['"True"', "'TRUE'", "'True'", 'true', "'true'", '"true"', 'True', '"TRUE"', 'TRUE']
        if True in [true_varient in response_text for true_varient in true_varients]:
            return True
        else:
            return False
    except Exception as Ex:
        print(Ex)
        # This is simpler method avoiding gemini rate limits
        mero_school_starting = ['meroschool', 'mero school', 'mero_school']
        return True in [m in post_content.lower() for m in mero_school_starting]



if __name__=="__main__":
    # Testing Few links
    post_content="""Mero school ko videos haru bhako jati share garum ta.

    maths I anyone?"""

    post_content='''
    Mero school ko videos haru bhako jati share garum ta 

    ma sanga ta chaina
    '''
    print(f'post_content:{post_content}\n\n is_mero_school_related_post:{is_mero_school_related_post(post_content)}')

    for i in range(1000):
        time.sleep(0.5)
        print(is_mero_school_related_post(post_content))