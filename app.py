from fastapi import (



    FastAPI,



    Request,



    Form,



    UploadFile,



    File



)



from fastapi.responses import HTMLResponse, RedirectResponse



from fastapi.templating import Jinja2Templates



from fastapi.staticfiles import StaticFiles



from starlette.middleware.sessions import SessionMiddleware







from supabase import create_client



from dotenv import load_dotenv







from werkzeug.utils import secure_filename







import os



import json



import joblib



import requests



import shutil



import pandas as pd



from sklearn.ensemble import RandomForestRegressor











# =========================================================



# LOAD ENVIRONMENT VARIABLES



# =========================================================







load_dotenv()







SUPABASE_URL = os.getenv("SUPABASE_URL")

SUPABASE_ANON_KEY = (

    os.getenv("SUPABASE_ANON_KEY")

    or os.getenv("SUPABASE_PUBLISHABLE_KEY")

)

SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")



OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")






OPENROUTER_MODEL = os.getenv(



    "OPENROUTER_MODEL",



    "openai/gpt-4o-mini"



)







FLASK_SECRET_KEY = os.getenv(



    "FLASK_SECRET_KEY",



    "student-ai-platform-secret"



)











# =========================================================



# FASTAPI APP



# =========================================================







app = FastAPI(



    title="Student AI Platform",



    description="AI-powered student academic platform",



    version="1.0.0"



)











# =========================================================



# SESSION



# =========================================================







app.add_middleware(



    SessionMiddleware,



    secret_key=FLASK_SECRET_KEY



)











# =========================================================



# STATIC FILES



# =========================================================







app.mount(



    "/static",



    StaticFiles(directory="static"),



    name="static"



)











# =========================================================



# TEMPLATES



# =========================================================







class LegacyTemplateResponseAdapter:







    def __init__(self, templates: Jinja2Templates):



        self.templates = templates







    def TemplateResponse(self, name, context):



        return self.templates.TemplateResponse(



            request=context["request"],



            name=name,



            context=context



        )











templates = LegacyTemplateResponseAdapter(



    Jinja2Templates(



        directory="templates"



    )



)











# =========================================================



# SUPABASE



# =========================================================







supabase = None

if SUPABASE_URL and SUPABASE_ANON_KEY:

    supabase = create_client(

        SUPABASE_URL,

        SUPABASE_ANON_KEY

    )



supabase_admin = None

if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:

    supabase_admin = create_client(

        SUPABASE_URL,

        SUPABASE_SERVICE_ROLE_KEY

    )



def get_db_client_for_write():

    if supabase_admin is not None:

        return supabase_admin

    if supabase is not None:

        return supabase

    raise RuntimeError(

        "Supabase is not configured. Set SUPABASE_URL, SUPABASE_ANON_KEY or SUPABASE_PUBLISHABLE_KEY, and SUPABASE_SERVICE_ROLE_KEY for database writes."

    )










# =========================================================



# ML MODEL



# =========================================================







BASE_DIR = os.path.dirname(os.path.abspath(__file__))



MODEL_PATH = os.path.join(BASE_DIR, "student_model.joblib")

DATASET_PATH = os.path.join(BASE_DIR, "data", "student_dataset_10000_rows.csv")





def train_model_from_dataset():

    dataset = pd.read_csv(DATASET_PATH)



    feature_columns = [

        "study_hours",

        "attendance",

        "sleep_hours",

        "internet_usage",

        "assignments_completed",

        "previous_score",

    ]



    X = dataset[feature_columns]

    y = dataset["exam_score"]



    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)

    if not os.getenv("VERCEL"):
        joblib.dump(model, MODEL_PATH)
    return model





model = None

MODEL_ERROR = None



try:

    model = joblib.load(MODEL_PATH)

except Exception as e:

    MODEL_ERROR = str(e)

    print("WARNING: Unable to load student_model.joblib")

    print("Model error:", e)



    try:

        model = train_model_from_dataset()

        MODEL_ERROR = None

        print("Model restored successfully from dataset.")

    except Exception as training_error:

        MODEL_ERROR = str(training_error)

        print("Model training failed:", training_error)









# =========================================================



# UPLOAD CONFIGURATION



# =========================================================







RESUME_FOLDER = (
    os.path.join("/tmp", "student-ai-platform", "uploads", "resumes")
    if os.getenv("VERCEL")
    else "uploads/resumes"
)







os.makedirs(



    RESUME_FOLDER,



    exist_ok=True



)











ALLOWED_RESUME_EXTENSIONS = {



    ".pdf",



    ".doc",



    ".docx"



}











# =========================================================



# QUIZ QUESTIONS



# =========================================================
# AI GENERATED QUIZ
# =========================================================



def generate_quiz_questions():



    if not OPENROUTER_API_KEY:
        raise Exception("OpenRouter API key is not configured.")



    unique_id = os.urandom(4).hex()



    prompt = f"""
Generate a fresh 5-question multiple-choice quiz for college students.

Fresh quiz ID: {unique_id}

Requirements:
- Questions must be randomly generated.
- Cover mixed CSE topics such as Python, Java, SQL, DSA,
  Machine Learning, AI, Web Development and Computer Science.
- Each question must have exactly 4 options.
- Only one option must be correct.
- Questions should be different from common repeated quiz questions.
- Keep the difficulty moderate.
- Do not include explanations.
- Return ONLY valid JSON.
- Do not use markdown or code fences.

Use exactly this JSON format:

{{
    "questions": [
        {{
            "id": "q1",
            "question": "Question text",
            "options": [
                "Option 1",
                "Option 2",
                "Option 3",
                "Option 4"
            ],
            "answer": "Option 1"
        }}
    ]
}}
"""



    response = ask_openrouter(prompt)



    response = response.strip()



    if response.startswith("```"):
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()



    data = json.loads(response)

    questions = data.get("questions", [])



    if len(questions) != 5:
        raise Exception("AI did not generate exactly 5 questions.")



    validated_questions = []



    for index, question in enumerate(questions, start=1):

        question_text = question.get("question")
        options = question.get("options")
        answer = question.get("answer")

        if not question_text:
            raise Exception("Generated question is invalid.")

        if not isinstance(options, list) or len(options) != 4:
            raise Exception("Each question must have exactly 4 options.")

        if answer not in options:
            raise Exception("Correct answer is not present in options.")

        validated_questions.append({
            "id": f"q{index}",
            "question": question_text,
            "options": options,
            "answer": answer
        })



    return validated_questions





# HELPER - CHECK LOGIN



# =========================================================







def get_current_user(request: Request):







    return request.session.get("user")











# =========================================================



# HOME



# =========================================================







@app.get(



    "/",



    response_class=HTMLResponse



)



async def home(request: Request):







    if get_current_user(request):







        return RedirectResponse(



            url="/dashboard",



            status_code=303



        )







    return RedirectResponse(



        url="/login",



        status_code=303



    )











# =========================================================



# REGISTER - GET



# =========================================================







@app.get(



    "/register",



    response_class=HTMLResponse



)



async def register_page(request: Request):







    return templates.TemplateResponse(



        "register.html",



        {



            "request": request,



            "full_name": "",



            "email": ""



        }



    )











def registration_error_message(error: Exception) -> str:



    message = str(getattr(error, "message", error))



    normalized_message = message.lower()







    if "rate limit" in normalized_message or "over_email_send_rate_limit" in normalized_message:



        return (



            "Supabase temporarily limited signup emails. "



            "Wait a few minutes before trying again, or check your "



            "Supabase Authentication email rate limits."



        )







    if "already registered" in normalized_message or "user_already_exists" in normalized_message:



        return (



            "An account with this email already exists. "



            "Please sign in or use password recovery."



        )







    print("Registration error:", error)



    return "Unable to create your account. Please try again."











# =========================================================



# REGISTER - POST



# =========================================================







@app.post(



    "/register",



    response_class=HTMLResponse



)



async def register(



    request: Request,



    full_name: str = Form(...),



    email: str = Form(...),



    password: str = Form(...)



):







    try:







        response = supabase.auth.sign_up({



            "email": email,



            "password": password,



            "options": {



                "data": {



                    "full_name": full_name.strip()



                }



            }



        })







        if not response.user:







            return templates.TemplateResponse(



                "register.html",



                {



                    "request": request,



                    "error":



                        "Supabase did not create the account. "



                        "Check your email confirmation settings and try again.",



                    "full_name": full_name,



                    "email": email



                }



            )







        return RedirectResponse(



            url="/login",



            status_code=303



        )







    except Exception as e:







        return templates.TemplateResponse(



            "register.html",



            {



                "request": request,



                "error": registration_error_message(e),



                "full_name": full_name,



                "email": email



            }



        )











# =========================================================



# LOGIN - GET



# =========================================================







@app.get(



    "/login",



    response_class=HTMLResponse



)



async def login_page(request: Request):







    return templates.TemplateResponse(



        "login.html",



        {



            "request": request,



            "error": None



        }



    )











# =========================================================



# LOGIN - POST



# =========================================================







@app.post(



    "/login",



    response_class=HTMLResponse



)



async def login(

    request: Request,

    email: str = Form(...),

    password: str = Form(...)

):



    authenticated_user = False



    try:







        response = supabase.auth.sign_in_with_password({



            "email": email,



            "password": password



        })







        if not response.user:







            return templates.TemplateResponse(



                "login.html",



                {



                    "request": request,



                    "error":



                        "Invalid email or password."



                }



            )



        authenticated_user = True

        save_authenticated_user_profile(

            response.session,

            response.user

        )



        request.session["user"] = {



            "id": response.user.id,



            "email": response.user.email



        }







        return RedirectResponse(



            url="/dashboard",



            status_code=303



        )







    except Exception as e:







        print(



            "Login error:",



            e



        )







        return templates.TemplateResponse(

            "login.html",

            {

                "request": request,

                "error":

                    (
                        "Your account was authenticated, but your profile "
                        "could not be saved. Check the profiles table's "
                        "INSERT and UPDATE RLS policies, then try again."
                        if authenticated_user
                        else "Invalid email or password."
                    )

            }



        )











# =========================================================



# LOGOUT



# =========================================================







@app.get("/logout")



async def logout(request: Request):







    try:







        supabase.auth.sign_out()







    except Exception:







        pass







    request.session.clear()







    return RedirectResponse(



        url="/login",



        status_code=303



    )











# =========================================================



# DASHBOARD



# =========================================================







@app.get(



    "/dashboard",



    response_class=HTMLResponse



)



async def dashboard(request: Request):







    user = get_current_user(request)







    if not user:







        return RedirectResponse(



            url="/login",



            status_code=303



        )







    user_id = user["id"]







    profile = {



        "full_name": "Student",



        "email": user["email"]



    }







    prediction_count = 0



    quiz_count = 0







    try:

        db = get_db_client_for_write()

        profile_response = (

            db

            .table("profiles")

            .select("full_name,email")

            .eq("id", user_id)

            .single()

            .execute()

        )






        if profile_response.data:







            profile = profile_response.data







    except Exception as e:







        print(



            "Profile error:",



            e



        )







    try:

        db = get_db_client_for_write()

        prediction_response = (

            db

            .table("predictions")

            .select("id")

            .eq("user_id", user_id)

            .execute()

        )






        prediction_count = len(



            prediction_response.data or []



        )







    except Exception as e:







        print(



            "Prediction count error:",



            e



        )







    try:

        db = get_db_client_for_write()

        quiz_response = (

            db

            .table("quiz_results")

            .select("id")

            .eq("user_id", user_id)

            .execute()

        )






        quiz_count = len(



            quiz_response.data or []



        )







    except Exception as e:







        print(



            "Quiz count error:",



            e



        )







    return templates.TemplateResponse(



        "dashboard.html",



        {



            "request": request,



            "profile": profile,



            "prediction_count": prediction_count,



            "quiz_count": quiz_count



        }



    )











# =========================================================



# PREDICTOR PAGE



# =========================================================







@app.get(



    "/predictor",



    response_class=HTMLResponse



)



async def predictor_page(request: Request):







    if not get_current_user(request):







        return RedirectResponse(



            url="/login",



            status_code=303



        )







    return templates.TemplateResponse(



        "predictor.html",



        {



            "request": request



        }



    )











# =========================================================



# PREDICTION



# =========================================================







@app.post(



    "/predict",



    response_class=HTMLResponse



)



async def predict(



    request: Request,



    study_hours: float = Form(...),



    attendance: float = Form(...),



    sleep_hours: float = Form(...),



    internet_usage: float = Form(...),



    assignments_completed: float = Form(...),



    previous_score: float = Form(...)



):







    user = get_current_user(request)







    if not user:







        return RedirectResponse(



            url="/login",



            status_code=303



        )







    # -----------------------------------------------------



    # MODEL CHECK



    # -----------------------------------------------------







    if model is None:







        return templates.TemplateResponse(



            "predictor.html",



            {



                "request": request,



                "error":



                    "The prediction model could not be loaded. "



                    "Please restore or retrain student_model.pkl."



            }



        )











    try:







        features = pd.DataFrame([

            {

                "study_hours": study_hours,

                "attendance": attendance,

                "sleep_hours": sleep_hours,

                "internet_usage": internet_usage,

                "assignments_completed": assignments_completed,

                "previous_score": previous_score,

            }

        ])











        # -------------------------------------------------



        # PREDICT



        # -------------------------------------------------







        prediction = model.predict(



            features



        )[0]







        prediction = max(



            0,



            min(100, prediction)



        )







        prediction = round(



            prediction,



            2



        )











        # -------------------------------------------------



        # PERFORMANCE



        # -------------------------------------------------







        if prediction >= 85:







            performance = "Excellent"







        elif prediction >= 70:







            performance = "Good"







        elif prediction >= 50:







            performance = "Average"







        else:







            performance = "Needs Improvement"











        # -------------------------------------------------



        # RECOMMENDATIONS



        # -------------------------------------------------







        recommendations = []











        if study_hours < 5:







            recommendations.append(



                "Try increasing your daily study hours."



            )











        if attendance < 75:







            recommendations.append(



                "Improve your class attendance."



            )











        if sleep_hours < 6:







            recommendations.append(



                "Maintain at least 6 hours of quality sleep."



            )











        if internet_usage > 6:







            recommendations.append(



                "Try reducing unnecessary internet usage."



            )











        if assignments_completed < 5:







            recommendations.append(



                "Complete more assignments regularly."



            )











        if previous_score < 60:







            recommendations.append(



                "Focus on improving your previous academic performance."



            )











        if not recommendations:







            recommendations.append(



                "Your current study habits look good. "



                "Keep maintaining consistency."



            )











        # -------------------------------------------------



        # FEATURE IMPORTANCE



        # -------------------------------------------------







        feature_names = [







            "Study Hours",



            "Attendance",



            "Sleep Hours",



            "Internet Usage",



            "Assignments Completed",



            "Previous Score"







        ]











        feature_importance = list(



            zip(



                feature_names,



                model.feature_importances_



            )



        )











        feature_importance.sort(



            key=lambda x: x[1],



            reverse=True



        )











        # -------------------------------------------------



        # SAVE TO SUPABASE



        # -------------------------------------------------







        try:

            db = get_db_client_for_write()

            db.table(

                "predictions"

            ).insert({






                "user_id":



                    user["id"],







                "study_hours":



                    study_hours,







                "attendance":



                    attendance,







                "sleep_hours":



                    sleep_hours,







                "internet_usage":



                    internet_usage,







                "assignments_completed":



                    assignments_completed,







                "previous_score":



                    previous_score,







                "predicted_score":



                    prediction,







                "performance":



                    performance







            }).execute()







        except Exception as e:







            print(



                "Prediction history error:",



                e



            )











        return templates.TemplateResponse(



            "result.html",



            {



                "request": request,



                "prediction": prediction,



                "predicted_score": prediction,



                "performance": performance,



                "recommendations": recommendations,



                "feature_importance": feature_importance



            }



        )











    except Exception as e:







        print(



            "Prediction error:",



            e



        )







        return templates.TemplateResponse(



            "predictor.html",



            {



                "request": request,



                "error":



                    "Please enter valid values."



            }



        )











# =========================================================



# PREDICTION HISTORY



# =========================================================







@app.get(



    "/history",



    response_class=HTMLResponse



)



async def history(request: Request):







    user = get_current_user(request)







    if not user:







        return RedirectResponse(



            url="/login",



            status_code=303



        )







    predictions = []







    try:

        db = get_db_client_for_write()

        response = (

            db

            .table("predictions")


            .select(



                "created_at,"



                "study_hours,"



                "attendance,"



                "sleep_hours,"



                "internet_usage,"



                "assignments_completed,"



                "previous_score,"



                "predicted_score,"



                "performance"



            )



            .eq(



                "user_id",



                user["id"]



            )



            .order(



                "created_at",



                desc=True



            )



            .execute()



        )







        predictions = response.data or []







    except Exception as e:







        print(



            "History error:",



            e



        )











    return templates.TemplateResponse(



        "history.html",



        {



            "request": request,



            "predictions": predictions



        }



    )











# =========================================================



# STUDY ASSISTANT



# =========================================================







@app.get(



    "/study-assistant",



    response_class=HTMLResponse



)



async def study_assistant_page(



    request: Request



):







    if not get_current_user(request):







        return RedirectResponse(



            url="/login",



            status_code=303



        )







    return templates.TemplateResponse(



        "study_assistant.html",



        {



            "request": request,



            "question": None,



            "answer": None,



            "error": None



        }



    )











# =========================================================



# STUDY ASSISTANT - ASK AI



# =========================================================







@app.post(



    "/study-assistant",



    response_class=HTMLResponse



)



async def study_assistant(



    request: Request,



    question: str = Form(...)



):







    if not get_current_user(request):







        return RedirectResponse(



            url="/login",



            status_code=303



        )











    question = question.strip()







    answer = None



    error = None











    if not question:







        error = "Please enter a question."











    elif not OPENROUTER_API_KEY:







        error = (



            "AI service is not configured. "



            "Please check your .env file."



        )











    else:







        try:







            answer = ask_openrouter(



                question



            )







        except Exception as e:







            print(



                "Study Assistant error:",



                e



            )







            error = (



                "Unable to get an AI response right now. "



                "Please try again."



            )











    return templates.TemplateResponse(



        "study_assistant.html",



        {



            "request": request,



            "question": question,



            "answer": answer,



            "error": error



        }



    )











# =========================================================



# OPENROUTER FUNCTION



# =========================================================







def save_authenticated_user_profile(auth_session, user):

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:

        raise RuntimeError(

            "Supabase URL or publishable key is not configured."

        )

    if not auth_session:

        raise RuntimeError(

            "Supabase did not return an authenticated session."

        )

    profile_client = create_client(

        SUPABASE_URL,

        SUPABASE_ANON_KEY

    )

    profile_client.auth.set_session(

        auth_session.access_token,

        auth_session.refresh_token

    )

    user_metadata = user.user_metadata or {}

    profile_client.table("profiles").upsert(

        {

            "id": user.id,

            "full_name": user_metadata.get("full_name", ""),

            "email": user.email

        },

        on_conflict="id"

    ).execute()


def ask_openrouter(question: str):







    url = (



        "https://openrouter.ai/api/v1/chat/completions"



    )











    headers = {







        "Authorization":



            f"Bearer {OPENROUTER_API_KEY}",







        "Content-Type":



            "application/json",







        "HTTP-Referer":



            "http://127.0.0.1:8000",







        "X-Title":



            "Student AI Platform"







    }











    system_prompt = """
You are the AI Study Assistant inside a Student AI Platform.

Help college students understand academic and technical
topics clearly.

Your answers should be:
- Beginner friendly
- Clear
- Practical
- Well structured
- Concise but useful

For programming questions:
- Explain the concept
- Give a simple example
- Provide clean code when useful

For study questions:
- Give practical study advice
- Break difficult topics into simple steps

Avoid unnecessary complexity.
"""











    payload = {







        "model":



            OPENROUTER_MODEL,







        "messages": [







            {



                "role":



                    "system",







                "content":



                    system_prompt



            },







            {



                "role":



                    "user",







                "content":



                    question



            }







        ],







        "temperature":



            0.5,







        "max_tokens":



            800







    }











    response = requests.post(







        url,







        headers=headers,







        json=payload,







        timeout=60







    )











    response.raise_for_status()











    data = response.json()











    return (



        data["choices"][0]



        ["message"]["content"]



    )











# =========================================================



# RESUME ANALYZER PAGE



# =========================================================







@app.get(



    "/resume-analyzer",



    response_class=HTMLResponse



)



async def resume_analyzer_page(



    request: Request



):







    if not get_current_user(request):







        return RedirectResponse(



            url="/login",



            status_code=303



        )







    return templates.TemplateResponse(



        "resume_analyzer.html",



        {



            "request": request,



            "analysis": None,



            "error": None



        }



    )











# =========================================================



# RESUME ANALYZER



# =========================================================







@app.post(



    "/analyze-resume",



    response_class=HTMLResponse



)



async def analyze_resume(



    request: Request,



    resume: UploadFile = File(...)



):







    if not get_current_user(request):







        return RedirectResponse(



            url="/login",



            status_code=303



        )











    filename = secure_filename(



        resume.filename or ""



    )











    extension = os.path.splitext(



        filename



    )[1].lower()











    if extension not in ALLOWED_RESUME_EXTENSIONS:







        return templates.TemplateResponse(



            "resume_analyzer.html",



            {



                "request": request,



                "analysis": None,



                "error":



                    "Please upload a PDF, DOC, or DOCX file."



            }



        )











    file_path = os.path.join(



        RESUME_FOLDER,



        filename



    )











    try:







        with open(



            file_path,



            "wb"



        ) as buffer:







            shutil.copyfileobj(



                resume.file,



                buffer



            )











        text = extract_resume_text(



            file_path,



            extension



        )











        if not text.strip():







            raise Exception(



                "No readable text found in resume."



            )











        analysis = analyze_resume_text(



            text



        )











                # -------------------------------------------------

        # SAVE RESUME ANALYSIS TO SUPABASE

        # -------------------------------------------------



        try:

            user = get_current_user(request)
            db = get_db_client_for_write()
            db.table(
                "resume_analyses"
            ).insert({
                "user_id": user["id"],

                "file_name": filename,

                "overview": analysis.get("overview", ""),

                "skills": analysis.get("skills", []),

                "missing_skills": analysis.get("missing_skills", []),

                "suggestions": analysis.get("suggestions", [])

            }).execute()



        except Exception as e:



            print(

                "Resume analysis history error:",

                e

            )





        return templates.TemplateResponse(



            "resume_analyzer.html",



            {



                "request": request,



                "analysis": analysis,



                "error": None



            }



        )











    except Exception as e:







        print(



            "Resume analysis error:",



            e



        )







        return templates.TemplateResponse(



            "resume_analyzer.html",



            {



                "request": request,



                "analysis": None,



                "error":



                    "Unable to analyze the resume. "



                    "Please check the uploaded file."



            }



        )











# =========================================================



# EXTRACT RESUME TEXT



# =========================================================







def extract_resume_text(



    file_path,



    extension



):







    if extension == ".pdf":







        from pypdf import PdfReader







        reader = PdfReader(



            file_path



        )







        text = ""







        for page in reader.pages:







            page_text = page.extract_text()







            if page_text:







                text += page_text + "\n"







        return text











    if extension == ".docx":







        from docx import Document







        document = Document(



            file_path



        )







        return "\n".join(



            paragraph.text



            for paragraph in document.paragraphs



        )











    if extension == ".doc":







        raise Exception(



            "Old .doc files are not supported yet. "



            "Please upload PDF or DOCX."



        )











    return ""











# =========================================================



# RESUME AI ANALYSIS



# =========================================================







def analyze_resume_text(text):







    if not OPENROUTER_API_KEY:







        return {







            "overview":



                "AI analysis is not configured.",







            "skills":



                [],







            "missing_skills":



                [],







            "suggestions":



                []







        }











    prompt = f"""
Analyze the following student resume.

Return a useful academic/career-oriented analysis.

Identify:
1. Resume overview
2. Technical skills found
3. Important missing skills
4. Improvement suggestions

Keep the response practical and concise.

Resume:

{text[:12000]}
"""











    response = ask_openrouter(



        prompt



    )











    return {







        "overview":



            response,







        "skills":



            [],







        "missing_skills":



            [],







        "suggestions":



            []







    }











# =========================================================



# QUIZ PAGE
# =========================================================



@app.get(
    "/quiz",
    response_class=HTMLResponse
)
async def quiz(request: Request):

    if not get_current_user(request):
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    try:

        questions = generate_quiz_questions()

        # Store generated questions for this quiz session
        request.session["quiz_questions"] = questions

        return templates.TemplateResponse(
            "quiz.html",
            {
                "request": request,
                "questions": questions
            }
        )

    except Exception as e:

        print("Quiz generation error:", e)

        return templates.TemplateResponse(
            "quiz.html",
            {
                "request": request,
                "questions": [],
                "error": "Unable to generate quiz questions. Please try again."
            }
        )



# =========================================================
# QUIZ SUBMIT
# =========================================================



@app.post(
    "/quiz-submit",
    response_class=HTMLResponse
)
async def quiz_submit(
    request: Request
):

    user = get_current_user(request)

    if not user:
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    form = await request.form()

    # Get the exact questions generated for this quiz
    quiz_questions = request.session.get(
        "quiz_questions",
        []
    )

    if not quiz_questions:
        return RedirectResponse(
            url="/quiz",
            status_code=303
        )

    score = 0
    results = []

    for question in quiz_questions:

        selected_answer = form.get(
            question["id"]
        )

        correct_answer = question["answer"]

        is_correct = (
            selected_answer == correct_answer
        )

        if is_correct:
            score += 1

        results.append({
            "question": question["question"],
            "selected": (
                selected_answer
                if selected_answer
                else "Not answered"
            ),
            "correct": correct_answer,
            "is_correct": is_correct
        })

    total_questions = len(
        quiz_questions
    )

    percentage = round(
        (score / total_questions) * 100,
        1
    )

    # -----------------------------------------------------
    # SAVE QUIZ RESULT
    # -----------------------------------------------------

    try:

        db = get_db_client_for_write()

        db.table(

            "quiz_results"

        ).insert({            "user_id": user["id"],
            "score": score,
            "total_questions": total_questions
        }).execute()

    except Exception as e:

        print(
            "Quiz history error:",
            e
        )

    # Clear quiz from session after submission
    request.session.pop(
        "quiz_questions",
        None
    )

    return templates.TemplateResponse(
        "quiz_result.html",
        {
            "request": request,
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "results": results
        }
    )



# SERVER START



# =========================================================







if __name__ == "__main__":







    import uvicorn







    uvicorn.run(



        "app:app",



        host="127.0.0.1",



        port=8000,



        reload=True



    )