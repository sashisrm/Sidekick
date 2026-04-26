from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.database import get_session
from db.models import Product, User, gen_uuid

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    category: str = ""
    version: str | None = None
    features: list[str] = []
    linked_document_ids: list[str] = []


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    version: str | None = None
    features: list[str] | None = None
    linked_document_ids: list[str] | None = None


class ProductOut(BaseModel):
    id: str
    name: str
    description: str
    category: str
    version: str | None
    features: list
    linked_document_ids: list
    created_at: str
    updated_at: str


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(
    body: ProductCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    product = Product(
        id=gen_uuid(),
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        category=body.category,
        version=body.version,
        features=body.features,
        linked_document_ids=body.linked_document_ids,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return _out(product)


@router.get("", response_model=list[ProductOut])
async def list_products(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Product).where(Product.user_id == current_user.id).order_by(Product.created_at.desc())
    )
    return [_out(p) for p in result.scalars().all()]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return _out(await _get(product_id, current_user.id, session))


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: str,
    body: ProductUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    product = await _get(product_id, current_user.id, session)
    if body.name is not None:
        product.name = body.name
    if body.description is not None:
        product.description = body.description
    if body.category is not None:
        product.category = body.category
    if body.version is not None:
        product.version = body.version
    if body.features is not None:
        product.features = body.features
    if body.linked_document_ids is not None:
        product.linked_document_ids = body.linked_document_ids
    await session.commit()
    await session.refresh(product)
    return _out(product)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    product = await _get(product_id, current_user.id, session)
    await session.delete(product)
    await session.commit()


async def _get(product_id: str, user_id: str, session: AsyncSession) -> Product:
    result = await session.execute(
        select(Product).where(Product.id == product_id, Product.user_id == user_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        name=p.name,
        description=p.description,
        category=p.category,
        version=p.version,
        features=p.features or [],
        linked_document_ids=p.linked_document_ids or [],
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )
