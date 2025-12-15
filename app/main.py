from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi import Form
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from app.database import get_db, engine
from app.models import (
    Base,
    KnowledgeBase,
    ChatLog,
    Category,
    Issue
)
from app.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    CategoryCreate,
    CategoryResponse,
    IssueCreate,
    IssueResponse
)


app = FastAPI(
    title="Платформа чат-ботов техподдержки",
    description="Веб-платформа для создания и управления чат-ботами технической поддержки",
    version="1.0.0"
)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

def find_answer(user_message: str, db: Session):
    records = db.query(KnowledgeBase).all()

    user_words = set(user_message.lower().split())

    for record in records:
        question_words = set(record.question.lower().split())
        if user_words & question_words:
            return record.answer

    return None


@app.get("/")
def root():
    return JSONResponse(
        content={"message": "Сервер чат-бот платформы запущен"},
        media_type="application/json; charset=utf-8"
    )


@app.post("/knowledge", response_model=KnowledgeBaseResponse)
def add_knowledge(item: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    knowledge = KnowledgeBase(
        question=item.question,
        answer=item.answer
    )
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    return knowledge


@app.post("/chat")
def chat(message: str, db: Session = Depends(get_db)):
    answer = find_answer(message, db)

    if answer:
        response = answer
    else:
        response = "Я передал ваш вопрос оператору. Пожалуйста, ожидайте."

    chat_log = ChatLog(
        user_message=message,
        bot_response=response
    )

    db.add(chat_log)
    db.commit()

    return {"response": response}


@app.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    new_category = Category(
        name=category.name,
        description=category.description
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@app.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()
 
@app.post("/issues", response_model=IssueResponse)
def create_issue(issue: IssueCreate, db: Session = Depends(get_db)):
    new_issue = Issue(
        title=issue.title,
        category_id=issue.category_id,
        knowledge_id=issue.knowledge_id
    )
    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)
    return new_issue


@app.get("/categories/{category_id}/issues", response_model=list[IssueResponse])
def get_issues(category_id: int, db: Session = Depends(get_db)):
    return db.query(Issue).filter(Issue.category_id == category_id).all()


@app.post("/issues/{issue_id}/select")
def select_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        return {"message": "Проблема не найдена"}

    if issue.knowledge:
        response = issue.knowledge.answer
    else:
        response = "К сожалению, подходящего ответа не найдено. Я передаю ваш вопрос оператору."

    chat_log = ChatLog(
        user_message=f"Выбранная проблема: {issue.title}",
        bot_response=response
    )

    db.add(chat_log)
    db.commit()

    return {
        "issue": issue.title,
        "response": response
    }

@app.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)):
    total = db.query(ChatLog).count()

    resolved = db.query(ChatLog).filter(
        ~ChatLog.bot_response.ilike("%оператор%")
    ).count()

    transferred = total - resolved

    return {
        "total_requests": total,
        "resolved_by_bot": resolved,
        "transferred_to_operator": transferred,
        "bot_efficiency_percent": round((resolved / total) * 100, 2) if total > 0 else 0
    }

@app.get("/analytics/issues")
def analytics_issues(db: Session = Depends(get_db)):
    result = (
        db.query(ChatLog.user_message, func.count(ChatLog.id).label("count"))
        .group_by(ChatLog.user_message)
        .order_by(func.count(ChatLog.id).desc())
        .all()
    )

    return [
        {"intent": row[0], "count": row[1]}
        for row in result
    ]

@app.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    knowledge = db.query(KnowledgeBase).all()
    issues = db.query(Issue).all()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "categories": categories,
            "knowledge": knowledge,
            "issues": issues
        }
    )

@app.post("/admin/categories")
def admin_create_category(
    name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    category = Category(
        name=name,
        description=description
    )
    db.add(category)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/knowledge")
def admin_create_knowledge(
    question: str = Form(...),
    answer: str = Form(...),
    db: Session = Depends(get_db)
):
    knowledge = KnowledgeBase(
        question=question,
        answer=answer
    )
    db.add(knowledge)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)
@app.post("/admin/issues")
def admin_create_issue(
    title: str = Form(...),
    category_id: int = Form(...),
    knowledge_id: int = Form(...),
    db: Session = Depends(get_db)
):
    issue = Issue(
        title=title,
        category_id=category_id,
        knowledge_id=knowledge_id
    )
    db.add(issue)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/issues/{issue_id}/delete")
def admin_delete_issue(
    issue_id: int,
    db: Session = Depends(get_db)
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if issue:
        db.delete(issue)
        db.commit()

    return RedirectResponse(url="/admin", status_code=303)
@app.post("/admin/knowledge/{knowledge_id}/delete")
def admin_delete_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db)
):
    knowledge = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == knowledge_id
    ).first()

    if knowledge:
        linked_issue = db.query(Issue).filter(
            Issue.knowledge_id == knowledge_id
        ).first()

        if not linked_issue:
            db.delete(knowledge)
            db.commit()

    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/issues/{issue_id}/edit")
def edit_issue_page(
    issue_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    categories = db.query(Category).all()
    knowledge = db.query(KnowledgeBase).all()

    return templates.TemplateResponse(
        "edit_issue.html",
        {
            "request": request,
            "issue": issue,
            "categories": categories,
            "knowledge": knowledge
        }
    )

@app.post("/admin/issues/{issue_id}/edit")
def update_issue(
    issue_id: int,
    title: str = Form(...),
    category_id: int = Form(...),
    knowledge_id: int = Form(...),
    db: Session = Depends(get_db)
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if issue:
        issue.title = title
        issue.category_id = category_id
        issue.knowledge_id = knowledge_id
        db.commit()

    return RedirectResponse(url="/admin", status_code=303)
@app.get("/admin/knowledge/{knowledge_id}/edit")
def edit_knowledge_page(
    knowledge_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    item = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == knowledge_id
    ).first()

    if not item:
        return RedirectResponse("/admin", status_code=303)

    return templates.TemplateResponse(
        "edit_knowledge.html",
        {
            "request": request,
            "item": item
        }
    )
@app.post("/admin/knowledge/{knowledge_id}/edit")
def update_knowledge(
    knowledge_id: int,
    question: str = Form(...),
    answer: str = Form(...),
    db: Session = Depends(get_db)
):
    item = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == knowledge_id
    ).first()

    if not item:
        return RedirectResponse("/admin", status_code=303)

    item.question = question
    item.answer = answer
    db.commit()

    return RedirectResponse("/admin", status_code=303)

Base.metadata.create_all(bind=engine)