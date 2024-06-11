def gemini_functions(post_title, comment_body):
    mero_school_varients = ['meroschool', 'mero-school', 'mero school', 'mero_school']
    
    return True in [varient in post_title.lower() or varient in comment_body.lower() for varient in mero_school_varients]