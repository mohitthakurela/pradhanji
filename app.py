from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import json
import os
import shutil
import uuid
from datetime import datetime
import uvicorn

app = FastAPI(title="Pradhan Ji Kisan Seva Kendra")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_FILE = "data.json"
UPLOAD_DIR = "static/uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Simple admin password - change this!
ADMIN_PASSWORD = "admin123"


def save_uploaded_file(upload_file: UploadFile) -> str:
    """Save uploaded file with unique name and return public URL path."""
    if not upload_file or not upload_file.filename:
        return ""
    ext = os.path.splitext(upload_file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return f"/static/uploads/{unique_name}"


# Pydantic Models
class Product(BaseModel):
    name: str
    description: str
    image: str
    packing: Optional[str] = ""
    category: str  # seeds, fertilizers
    in_stock: bool = True


class GalleryItem(BaseModel):
    image: str
    caption: Optional[str] = ""


class Inquiry(BaseModel):
    name: str
    phone: str
    message: str


# Data persistence
def load_data():
    if not os.path.exists(DATA_FILE):
        default = {
            "seeds": [
                {"id": 1, "name": "गेहूँ का बीज (HD 2967 - IARI)", "description": "यह गेहूँ की उन्नत किस्म है जो प्रति एकड़ 25-30 क्विंटल पैदावार देती है।", "image": "/static/wheat_bag.jpg", "packing": "40 Kg बैग", "in_stock": True},
                {"id": 2, "name": "धान का बीज (Pusa Basmati 1121)", "description": "बासमती धान की सबसे बेहतरीन किस्म। लंबे, खुशबूदार चावल।", "image": "/static/paddy_bag.jpg", "packing": "10 Kg बैग", "in_stock": True},
                {"id": 3, "name": "सरसों का बीज (Pioneer 45S46)", "description": "उच्च तेल प्रतिशत (42%+) वाली हाइब्रिड सरसों। झुलसा बीमारी से बचाव और अधिक शाखाएँ।", "image": "/static/mustard_packet.jpg", "packing": "1 Kg बैग", "in_stock": True}
            ],
            "fertilizers": [
                {"id": 1, "name": "सरकारी यूरिया (Neem Coated Urea - IFFCO)", "description": "फसल में हरियाली और नाइट्रोजन की पूर्ति के लिए 100% नीम कोटेड यूरिया।", "image": "/static/urea_bag.jpg", "packing": "45 Kg बैग", "in_stock": True},
                {"id": 2, "name": "DAP खाद (IFFCO / KRIBHCO)", "description": "फास्फोरस और नाइट्रोजन का उत्तम संतुलन। बोआई के समय जड़ों की मजबूती के लिए अति आवश्यक।", "image": "/static/dap_bag.jpg", "packing": "50 Kg बैग", "in_stock": True},
                {"id": 3, "name": "जिंक सल्फेट 33% (Mono Zinc)", "description": "धान में खैरा बीमारी और फसलों में पीलापन दूर करने के लिए अति सूक्ष्म पोषक तत्व।", "image": "/static/zinc_packet.jpg", "packing": "4 Kg बैग", "in_stock": True},
                {"id": 4, "name": "कीटनाशक (Coragen - Katyayani / FMC)", "description": "इल्ली, तना छेदक व इल्लियों पर लंबे समय तक असरदार नियंत्रण। धान, गन्ना व सब्जियों के लिए सर्वोत्तम।", "image": "/static/pesticide_bottle.jpg", "packing": "150 ml बॉटल", "in_stock": True}
            ],
            "gallery": [
                {"id": 1, "image": "/static/shop.jpg", "caption": "Shop View 1"},
                {"id": 2, "image": "/static/shop2.jpg", "caption": "Shop View 2"},
                {"id": 3, "image": "/static/owner.jpg", "caption": "Owner"}
            ],
            "inquiries": []
        }
        save_data(default)
        return default
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "inquiries" not in data:
            data["inquiries"] = []
        return data


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def next_id(items):
    return max([i["id"] for i in items], default=0) + 1


# ============== PUBLIC ROUTES ==============
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = load_data()
    featured = []
    for cat in ["fertilizers", "seeds"]:
        if cat in data:
            for p in data[cat][:3]:
                item = dict(p)
                item["category"] = cat
                featured.append(item)
    return templates.TemplateResponse(request, "index.html", {
        "featured": featured,
        "gallery": data.get("gallery", [])
    })


@app.post("/", response_class=HTMLResponse)
async def home_post(request: Request,
                    name: str = Form(...),
                    phone: str = Form(...),
                    message: str = Form(...)):
    data = load_data()
    new_inquiry = {
        "id": next_id(data.get("inquiries", [])),
        "name": name,
        "phone": phone,
        "message": message,
        "date": datetime.now().strftime("%Y-%m-%d %I:%M %p")
    }
    if "inquiries" not in data:
        data["inquiries"] = []
    data["inquiries"].insert(0, new_inquiry)
    save_data(data)

    featured = []
    for cat in ["fertilizers", "seeds"]:
        if cat in data:
            for p in data[cat][:3]:
                item = dict(p)
                item["category"] = cat
                featured.append(item)
    return templates.TemplateResponse(request, "index.html", {
        "featured": featured,
        "gallery": data.get("gallery", []),
        "success": True
    })


@app.post("/api/inquiry/submit")
async def submit_inquiry_api(
    name: str = Form(...),
    phone: str = Form(...),
    message: str = Form(...)
):
    data = load_data()
    new_inquiry = {
        "id": next_id(data.get("inquiries", [])),
        "name": name,
        "phone": phone,
        "message": message,
        "date": datetime.now().strftime("%Y-%m-%d %I:%M %p")
    }
    if "inquiries" not in data:
        data["inquiries"] = []
    data["inquiries"].insert(0, new_inquiry)
    save_data(data)
    return JSONResponse({"status": "success", "message": "आपका संदेश सफलतापूर्वक प्राप्त हो गया है!"})


@app.get("/seeds", response_class=HTMLResponse)
async def seeds_page(request: Request):
    data = load_data()
    return templates.TemplateResponse(request, "seeds.html", {
        "products": data.get("seeds", [])
    })


@app.get("/fertilizers", response_class=HTMLResponse)
async def fertilizers_page(request: Request):
    data = load_data()
    return templates.TemplateResponse(request, "fertilizers.html", {
        "products": data.get("fertilizers", [])
    })


# ============== ADMIN PANEL ==============
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, password: str = ""):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("""
            <html><body style="font-family:sans-serif;padding:40px;background:#f5f5f5;">
            <div style="max-width:400px;margin:100px auto;background:white;padding:30px;border-radius:10px;box-shadow:0 4px 12px rgba(0,0,0,0.1);">
            <h2 style="color:#16a34a;">Admin Login</h2>
            <form method="get" action="/admin">
                <input type="password" name="password" placeholder="Enter admin password"
                    style="width:100%;padding:12px;margin:15px 0;border:1px solid #ddd;border-radius:5px;font-size:1rem;" required>
                <button type="submit"
                    style="background:#1a8844;color:white;padding:12px 25px;border:none;border-radius:5px;cursor:pointer;font-size:1rem;width:100%;">
                    Login
                </button>
            </form>
            <p style="color:#666;font-size:0.85rem;margin-top:15px;">Default password: admin123</p>
            </div></body></html>
        """)
    data = load_data()
    return templates.TemplateResponse(request, "admin.html", {
        "data": data,
        "password": password
    })


# ============== PRODUCT CRUD APIS ==============
@app.post("/api/product/add")
async def add_product(
    password: str = Form(...),
    category: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    image: str = Form(""),
    image_file: Optional[UploadFile] = File(None),
    packing: str = Form(""),
    in_stock: Optional[str] = Form("on")
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Wrong password")
    if category not in ["seeds", "fertilizers"]:
        raise HTTPException(status_code=400, detail="Invalid category")

    final_image = image
    if image_file and image_file.filename:
        final_image = save_uploaded_file(image_file)

    if not final_image:
        raise HTTPException(status_code=400, detail="Image URL or file required")

    data = load_data()
    if category not in data:
        data[category] = []

    new_product = {
        "id": next_id(data[category]),
        "name": name,
        "description": description,
        "image": final_image,
        "packing": packing,
        "in_stock": True if in_stock in ["on", "true", "True", True] else False
    }
    data[category].append(new_product)
    save_data(data)
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


@app.post("/api/product/update")
async def update_product(
    password: str = Form(...),
    category: str = Form(...),
    id: int = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    image: str = Form(""),
    image_file: Optional[UploadFile] = File(None),
    packing: str = Form(""),
    in_stock: Optional[str] = Form(None)
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Wrong password")

    final_image = image
    if image_file and image_file.filename:
        final_image = save_uploaded_file(image_file)

    data = load_data()
    if category in data:
        for item in data[category]:
            if item["id"] == id:
                item["name"] = name
                item["description"] = description
                if final_image:
                    item["image"] = final_image
                item["packing"] = packing
                item["in_stock"] = True if in_stock in ["on", "true", "True", True] else False
                break
    save_data(data)
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)




@app.post("/api/product/delete")
async def delete_product(
    password: str = Form(...),
    category: str = Form(...),
    id: int = Form(...)
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Wrong password")
    data = load_data()
    data[category] = [i for i in data[category] if i["id"] != id]
    save_data(data)
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


# ============== GALLERY CRUD APIS ==============
@app.post("/api/gallery/add")
async def add_gallery(
    password: str = Form(...),
    image: str = Form(""),
    image_file: Optional[UploadFile] = File(None),
    caption: str = Form("")
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Wrong password")

    final_image = image
    if image_file and image_file.filename:
        final_image = save_uploaded_file(image_file)

    if not final_image:
        raise HTTPException(status_code=400, detail="Image URL or file required")

    data = load_data()
    data["gallery"].append({
        "id": next_id(data["gallery"]),
        "image": final_image,
        "caption": caption
    })
    save_data(data)
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


@app.post("/api/gallery/update")
async def update_gallery(
    password: str = Form(...),
    id: int = Form(...),
    image: str = Form(""),
    image_file: Optional[UploadFile] = File(None),
    caption: str = Form("")
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Wrong password")

    final_image = image
    if image_file and image_file.filename:
        final_image = save_uploaded_file(image_file)

    data = load_data()
    for item in data["gallery"]:
        if item["id"] == id:
            if final_image:
                item["image"] = final_image
            item["caption"] = caption
            break
    save_data(data)
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


@app.post("/api/gallery/delete")
async def delete_gallery(
    password: str = Form(...),
    id: int = Form(...)
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Wrong password")
    data = load_data()
    data["gallery"] = [i for i in data["gallery"] if i["id"] != id]
    save_data(data)
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


# ============== INQUIRY CRUD APIS ==============
@app.post("/api/inquiry/delete")
async def delete_inquiry(
    password: str = Form(...),
    id: int = Form(...)
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Wrong password")
    data = load_data()
    data["inquiries"] = [i for i in data.get("inquiries", []) if i["id"] != id]
    save_data(data)
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


if __name__ == "__main__":
    uvicorn.run("app:app", port=8000, reload=True)

