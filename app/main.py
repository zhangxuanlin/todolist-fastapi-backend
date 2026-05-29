import asyncio
import json
import os
from pathlib import Path
from fastapi import FastAPI, Query, Path as FastAPIPath, Body, Cookie, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from collections.abc import AsyncIterable, Iterable
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.users import router as users_router
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "app" / "uploads"

app = FastAPI(
    title="🤖 AI Agent 系统",
    description="""
    ## 欢迎使用 Agent 核心业务接口文档
    本系统集成了 LangChain / LangGraph 状态机，提供高并发的图文分析与智能路由调度能力。
    * 📌 **通用规范**：所有接口默认返回标准 JSON 格式。
    * 🔐 **认证机制**：请先在右上角 Authorize 中注入由 Java 网关分发的 JWT Token。
    """,
    version="1.0.10"
)
# 允许任何源、任何方法、任何请求头
app.add_middleware(
    CORSMiddleware,
    # ✅ 正确：只放行你真正的 Vercel 前端域名（注意：结尾千万不要加斜杠 /）
    allow_origins=["https://totolist-fastapi-frontend.vercel.app", "http://localhost:3000"],       
    # ✅ 正确：既然是具体域名，这里强烈建议设为 True！
    # 这样前端后续在 Headers 里传 Authorization 或 Cookie 时才不会被拦截
    allow_credentials=True,   
    allow_methods=["*"],       
    allow_headers=["*"],
)

app.include_router(users_router)

# 挂载上传文件目录
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


tags=["📦 商品管理模块", "车间管理"]

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

message = """
Rick: (stumbles in drunkenly, and turns on the lights) Morty! You gotta come on. You got--... you gotta come with me.
Morty: (rubs his eyes) What, Rick? What's going on?
Rick: I got a surprise for you, Morty.
Morty: It's the middle of the night. What are you talking about?
Rick: (spills alcohol on Morty's bed) Come on, I got a surprise for you. (drags Morty by the ankle) Come on, hurry up. (pulls Morty out of his bed and into the hall)
Morty: Ow! Ow! You're tugging me too hard!
Rick: We gotta go, gotta get outta here, come on. Got a surprise for you Morty.
"""


class ItemCreateDTO(BaseModel):
    # title、description 等参数会直接显示在 Swagger 的 Request Body Schema 中
    item_id: str = Field(
        description="商品id：必须是唯一的商品id，不能包含特殊字符", 
        example="123456"
    )

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

class Item1(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


class Item2(BaseModel):
    name: str = Field(title="这是名称", description="这是名称111")
    description: str | None = Field(
        default=None, title="这是描述", description="这是描述", max_length=300
    )
    price: float = Field(gt=0, description="这是价格")
    tax: float | None = None

class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@app.get("/", description="商品管理模块", tags=[tags[0]])
def read_root():
    return {"Hello": "World"}

@app.get("/items/stream")
async def stream_items():
    async def item_data_generator():
        items_data = [
            {"name": "Plumbus", "description": "A multi-purpose household device."},
            {"name": "Portal Gun", "description": "A portal opening device."},
            {"name": "Meeseeks Box", "description": "A box that summons a Meeseeks."},
        ]
        for item in items_data:
            json_str = json.dumps(item, ensure_ascii=False)
            yield f"data: {json_str}\n\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(item_data_generator(), media_type="text/event-stream")

@app.get(
    "/items/{item_id}",
    description="这是商品详情路径",
    summary="这是商品详情路径",
    tags=[tags[0]],
    response_model=ItemCreateDTO
)
def read_item(item_id: int):
    """
    这是商品详情路径
    """
    return {"item_id": item_id}

@app.post("/items/", description="这是创建商品路径", summary="这是创建商品路径", tags=[tags[0]])
def create_item(item: Item):
    return item

@app.get("/items/", tags=[tags[1]])
async def read_item(skip: int = 0, limit: int = 10):
    return {
        "data": fake_items_db[skip : skip + limit],
        "code": 200,
        "total": len(fake_items_db),
    }

# 更新商品
@app.put("/items/{item_id}", tags=[tags[1]])
def update_item(item_id: int, item: Item):
    return {"item_id": item_id, "item_name": item.name}

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}

@app.post("/items1/")
async def create_item(item: Item1):
    return item

@app.put("/items2/{item_id}")
async def update_item(item_id: int, item: Item1):
    return {"item_id": item_id, **item.model_dump()}

@app.get("/items3/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

@app.put("/items4/{item_id}")
async def update_item(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=0, le=1000)],
    q: str | None = None,
    item: Item | None = None,
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if item:
        results.update({"item": item})
    return {"message": "Item updated"}

@app.put("/items5/{item_id}")
async def update_item(item_id: int, item: Annotated[Item2, Body(embed=True)]):
    results = {"item_id": item_id, "item": item}
    return results


@app.get("/items6/")
async def read_items(ads_id: Annotated[str | None, Cookie()] = None):
    return {"ads_id": ads_id}

@app.post("/items7/")
async def create_item(item: Item) -> Item:
    return item


@app.get("/items8/")
async def read_items() -> list[Item]:
    return [
        Item(name="Portal Gun", price=42.0),
        Item(name="Plumbus", price=32.0),
    ]

@app.post("/items9/", status_code=status.HTTP_504_GATEWAY_TIMEOUT)
async def create_item(name: str):
    return {"name": name}

# 1. 定义一个异步生成器，用来“模拟大模型一句一句往外蹦”
async def script_streamer():
    # 按照换行符拆分台词
    lines = message.split("\n")
    
    for line in lines:
        if line.strip():
            # SSE 协议的标准格式必须以 "data: " 开头，以 "\n\n" 结尾
            yield f"data: {line}\n\n"
            # 模拟网络延迟或大模型思考，每吐出一句台词，憋 0.8 秒
            await asyncio.sleep(0.8)


# 2. 编写流式输出接口
@app.get("/stream/rick", summary="🚀 瑞克与莫蒂台词流式输出", tags=["流式传输模块"])
async def get_rick_stream():
    """
    该接口使用 SSE (Server-Sent Events) 技术，
    如同 ChatGPT 打字机一般，异步分批次返回文本数据。
    """
    # 使用 StreamingResponse 包裹生成器
    # media_type 必须指定为 "text/event-stream"
    return StreamingResponse(script_streamer(), media_type="text/event-stream")


def get_full_name(first_name: str, last_name: str):
    full_name = first_name.title() + " " + last_name.title()
    return full_name

def get_name_with_age(name: str, age: int):
    full_name = name.title() + ": " + str(age)
    return full_name

def process_items(items: list[str]):
    for item in items:
        print(item)

def process_items1(prices: dict[str, float]):
    for item_name, item_price in prices.items():
        print(item_name, item_price)

def say_hi(name: str | None = None):
    if name is not None:
        print(f"hi, {name}")
    else:
        print("hi, world")

# say_hi("john")
# say_hi()



# print(get_full_name("john", "doe"))
# print(get_name_with_age("john", 30))
# # process_items(["1", "2", "3"])
# process_items1({"a": 1, "b": 2, "c": 3})

class User(BaseModel):
    id: int
    name: str = "John Doe"
    signup_ts: datetime | None = None
    friends: list[int] = []


external_data = {
    "id": "123",
    "signup_ts": "2017-06-01",
    "friends": [1, "2", b"3"],
}
user = User(**external_data)
# print(user)
# print(user.id)
