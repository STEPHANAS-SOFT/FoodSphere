from fastapi import HTTPException, status
from dataclasses import dataclass
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from ..models import (
    User, Vendor, Item, ItemCategory, DeliveryAddress, 
    Rider, Order, ItemAddonGroup, ItemAddon, 
    ItemVariation, OrderItem, OrderItemAddon, OrderTracking, 
    Cart, CartItem, CartItemAddon, UserWallet, VendorWallet, 
    RiderWallet, WalletTransaction
)
from uuid import UUID


# ==============================================================================================================
#                                           USERS HANDLERS AND QUERIES
# ==============================================================================================================

# GET ALL USERS
@dataclass(frozen=True)
class GetAllUserQuery:
    pass


class GetAllUserQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllUserQuery, skip: int = 0, limit: int = 10):
        all_user = (self.db.query(User)
                    .offset(skip).limit(limit).all()
                   )
        if not all_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return all_user
    


# GET USER BY ID
@dataclass(frozen=True)
class GetUserByIdQuery:
    user_id: UUID


class GetUserByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetUserByIdQuery):
        user = self.db.query(User).filter(User.id == query.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with ID {0} not found".format(query.user_id))
        return user
    


# ==============================================================================================================
#                                           VENDOR HANDLERS AND QUERIES
# ==============================================================================================================

# GET ALL VENDORS
@dataclass(frozen=True)
class GetAllVendorQuery:
    pass


class GetAllVendorQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllVendorQuery, skip: int = 0, limit: int = 10):
        all_vendors = (self.db.query(Vendor)
                    .offset(skip).limit(limit).all()
                   )
        
        if not all_vendors:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        return all_vendors


# GET VENDOR BY ID
@dataclass
class GetVendorByIdQuery:
    vendor_id: int

class GetVendorByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetVendorByIdQuery):

        vendor = (
                 self.db.query(Vendor)
                .options(joinedload(Vendor.items))
                .filter(Vendor.id == query.vendor_id)
                .first()
        )

        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor with ID {0} not found".format(query.vendor_id))
        return vendor
    


# ==========================
# GET VENDOR BY NAME
# ==========================
@dataclass(frozen=True)
class GetVendorByNameQuery:
    name: str


class GetVendorByNameQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetVendorByNameQuery):
        vendor_list = self.db.query(Vendor).filter(Vendor.name.ilike(f"%{query.name}%")).all()
        if not vendor_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor by name: {0} not found".format(query.name))
        return vendor_list




# ==============================================================================================================
#                                           ITEM HANDLERS AND QUERIES
# ==============================================================================================================
# ==========================
# GET ALL ITEMS
# ==========================
@dataclass(frozen=True)
class GetAllItemQuery:
    pass


class GetAllItemQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllItemQuery, skip: int = 0, limit: int = 10):
        all_items = (self.db.query(Item)
                    .offset(skip).limit(limit).all()
                   )
        if not all_items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Items not found")
        return all_items


# ==========================
# GET ITEM BY ID
# ==========================
@dataclass
class GetItemByIdQuery:
    item_id: int

class GetItemByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemByIdQuery):
        item = self.db.query(Item).filter(Item.id == query.item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item with ID {0} not found".format(query.item_id))
        return item
    


# ==========================
# GET ITEM BY NAME
# ==========================
@dataclass(frozen=True)
class GetItemByNameQuery:
    name: str


class GetItemByNameQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemByNameQuery):
        item_list = self.db.query(Item).filter(Item.name.ilike(f"%{query.name}%")).all()
        if not item_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item by name: {0} not found".format(query.name))
        return item_list


# ==============================================================================================================
#                                           ITEM CATEGORY HANDLERS AND QUERIES
# ==============================================================================================================

@dataclass(frozen=True)
class GetAllItemCategoryQuery:
    pass

class GetAllItemCategoryQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllItemCategoryQuery, skip: int = 0, limit: int = 10):
        all_categories = self.db.query(ItemCategory).offset(skip).limit(limit).all()
        if not all_categories:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categories not found")
        return all_categories

@dataclass
class GetItemCategoryByIdQuery:
    category_id: int

class GetItemCategoryByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemCategoryByIdQuery):
        category = self.db.query(ItemCategory).filter(ItemCategory.id == query.category_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category with ID {0} not found".format(query.category_id))
        return category

@dataclass(frozen=True)
class GetItemCategoryByNameQuery:
    name: str

class GetItemCategoryByNameQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemCategoryByNameQuery):
        category_list = self.db.query(ItemCategory).filter(ItemCategory.name.ilike(f"%{query.name}%")).all()
        if not category_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category by name: {0} not found".format(query.name))
        return category_list


# ==============================================================================================================
#                                           DELIVERY ADDRESS HANDLERS AND QUERIES
# ==============================================================================================================

@dataclass(frozen=True)
class GetAllDeliveryAddressQuery:
    pass

class GetAllDeliveryAddressQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllDeliveryAddressQuery, skip: int = 0, limit: int = 10):
        all_addresses = self.db.query(DeliveryAddress).offset(skip).limit(limit).all()
        if not all_addresses:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addresses not found")
        return all_addresses

@dataclass
class GetDeliveryAddressByIdQuery:
    address_id: int

class GetDeliveryAddressByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetDeliveryAddressByIdQuery):
        address = self.db.query(DeliveryAddress).filter(DeliveryAddress.id == query.address_id).first()
        if not address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address with ID {0} not found".format(query.address_id))
        return address

@dataclass(frozen=True)
class GetDeliveryAddressByUserIdQuery:
    user_id: int

class GetDeliveryAddressByUserIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetDeliveryAddressByUserIdQuery):
        addresses = self.db.query(DeliveryAddress).filter(DeliveryAddress.user_id == query.user_id).all()
        if not addresses:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addresses for user ID {0} not found".format(query.user_id))
        return addresses


# ==============================================================================================================
#                                           RIDER HANDLERS AND QUERIES
# ==============================================================================================================

@dataclass(frozen=True)
class GetAllRiderQuery:
    pass

class GetAllRiderQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllRiderQuery, skip: int = 0, limit: int = 10):
        all_riders = self.db.query(Rider).offset(skip).limit(limit).all()
        if not all_riders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Riders not found")
        return all_riders

@dataclass
class GetRiderByIdQuery:
    rider_id: int

class GetRiderByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetRiderByIdQuery):
        rider = self.db.query(Rider).filter(Rider.id == query.rider_id).first()
        if not rider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rider with ID {0} not found".format(query.rider_id))
        return rider

@dataclass(frozen=True)
class GetRiderByNameQuery:
    name: str

class GetRiderByNameQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetRiderByNameQuery):
        rider_list = self.db.query(Rider).filter(Rider.full_name.ilike(f"%{query.name}%")).all()
        if not rider_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rider by name: {0} not found".format(query.name))
        return rider_list


# ==============================================================================================================
#                                           ITEM ADDON GROUP HANDLERS AND QUERIES
# ==============================================================================================================

@dataclass(frozen=True)
class GetAllItemAddonGroupQuery:
    pass

class GetAllItemAddonGroupQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllItemAddonGroupQuery, skip: int = 0, limit: int = 10):
        all_groups = self.db.query(ItemAddonGroup).offset(skip).limit(limit).all()
        if not all_groups:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addon groups not found")
        return all_groups

@dataclass
class GetItemAddonGroupByIdQuery:
    group_id: int

class GetItemAddonGroupByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemAddonGroupByIdQuery):
        group = self.db.query(ItemAddonGroup).filter(ItemAddonGroup.id == query.group_id).first()
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addon group with ID {0} not found".format(query.group_id))
        return group

@dataclass(frozen=True)
class GetItemAddonGroupByItemIdQuery:
    item_id: int

class GetItemAddonGroupByItemIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemAddonGroupByItemIdQuery):
        groups = self.db.query(ItemAddonGroup).filter(ItemAddonGroup.item_id == query.item_id).all()
        if not groups:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addon groups for item ID {0} not found".format(query.item_id))
        return groups


# ==============================================================================================================
#                                           ITEM ADDON HANDLERS AND QUERIES
# ==============================================================================================================

@dataclass(frozen=True)
class GetAllItemAddonQuery:
    pass

class GetAllItemAddonQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllItemAddonQuery, skip: int = 0, limit: int = 10):
        all_addons = self.db.query(ItemAddon).offset(skip).limit(limit).all()
        if not all_addons:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addons not found")
        return all_addons

@dataclass
class GetItemAddonByIdQuery:
    addon_id: int

class GetItemAddonByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemAddonByIdQuery):
        addon = self.db.query(ItemAddon).filter(ItemAddon.id == query.addon_id).first()
        if not addon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addon with ID {0} not found".format(query.addon_id))
        return addon

@dataclass(frozen=True)
class GetItemAddonByGroupIdQuery:
    group_id: int

class GetItemAddonByGroupIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemAddonByGroupIdQuery):
        addons = self.db.query(ItemAddon).filter(ItemAddon.group_id == query.group_id).all()
        if not addons:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Addons for group ID {0} not found".format(query.group_id))
        return addons


# ==============================================================================================================
#                                           ITEM VARIATION HANDLERS AND QUERIES
# ==============================================================================================================

@dataclass(frozen=True)
class GetAllItemVariationQuery:
    pass

class GetAllItemVariationQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllItemVariationQuery, skip: int = 0, limit: int = 10):
        all_variations = self.db.query(ItemVariation).offset(skip).limit(limit).all()
        if not all_variations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variations not found")
        return all_variations

@dataclass
class GetItemVariationByIdQuery:
    variation_id: int

class GetItemVariationByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemVariationByIdQuery):
        variation = self.db.query(ItemVariation).filter(ItemVariation.id == query.variation_id).first()
        if not variation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variation with ID {0} not found".format(query.variation_id))
        return variation

@dataclass(frozen=True)
class GetItemVariationByItemIdQuery:
    item_id: int

class GetItemVariationByItemIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemVariationByItemIdQuery):
        variations = self.db.query(ItemVariation).filter(ItemVariation.item_id == query.item_id).all()
        if not variations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variations for item ID {0} not found".format(query.item_id))
        return variations


# ==============================================================================================================
#                                           ORDER HANDLERS AND QUERIES
# ==============================================================================================================

@dataclass(frozen=True)
class GetAllOrderQuery:
    pass

class GetAllOrderQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllOrderQuery, skip: int = 0, limit: int = 10):
        all_orders = (
            self.db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.addons),
                joinedload(Order.tracking)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        if not all_orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orders not found")
        return all_orders

@dataclass
class GetOrderByIdQuery:
    order_id: int

class GetOrderByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetOrderByIdQuery):
        order = (
            self.db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.addons),
                joinedload(Order.tracking)
            )
            .filter(Order.id == query.order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order with ID {0} not found".format(query.order_id))
        return order

@dataclass(frozen=True)
class GetOrderByUserIdQuery:
    user_id: int

class GetOrderByUserIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetOrderByUserIdQuery):
        orders = (
            self.db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.addons),
                joinedload(Order.tracking)
            )
            .filter(Order.user_id == query.user_id)
            .all()
        )
        if not orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orders for user ID {0} not found".format(query.user_id))
        return orders

@dataclass(frozen=True)
class GetOrderByVendorIdQuery:
    vendor_id: int

class GetOrderByVendorIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetOrderByVendorIdQuery):
        orders = (
            self.db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.addons),
                joinedload(Order.tracking)
            )
            .filter(Order.vendor_id == query.vendor_id)
            .all()
        )
        if not orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orders for vendor ID {0} not found".format(query.vendor_id))
        return orders

@dataclass(frozen=True)
class GetOrderByRiderIdQuery:
    rider_id: int

class GetOrderByRiderIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetOrderByRiderIdQuery):
        orders = (
            self.db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.addons),
                joinedload(Order.tracking)
            )
            .filter(Order.rider_id == query.rider_id)
            .all()
        )
        if not orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orders for rider ID {0} not found".format(query.rider_id))
        return orders


# ==============================================================================================================
#                                           CART HANDLERS AND QUERIES
# ==============================================================================================================

@dataclass(frozen=True)
class GetAllCartQuery:
    pass

class GetAllCartQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllCartQuery, skip: int = 0, limit: int = 10):
        all_carts = (
            self.db.query(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.addons))
            .offset(skip)
            .limit(limit)
            .all()
        )
        if not all_carts:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carts not found")
        return all_carts

@dataclass
class GetCartByIdQuery:
    cart_id: int

class GetCartByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetCartByIdQuery):
        cart = (
            self.db.query(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.addons))
            .filter(Cart.id == query.cart_id)
            .first()
        )
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart with ID {0} not found".format(query.cart_id))
        return cart

@dataclass(frozen=True)
class GetCartByUserIdQuery:
    user_id: int

class GetCartByUserIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetCartByUserIdQuery):
        carts = (
            self.db.query(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.addons))
            .filter(Cart.user_id == query.user_id)
            .all()
        )
        if not carts:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carts for user ID {0} not found".format(query.user_id))
        return carts


# ==============================================================================================================
#                                           WALLET HANDLERS AND QUERIES
# ==============================================================================================================

# GET WALLET BALANCE
@dataclass(frozen=True)
class GetWalletBalanceQuery:
    wallet_type: str  # "user", "vendor", or "rider"
    owner_id: int

class GetWalletBalanceQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetWalletBalanceQuery):
        wallet = None
        
        if query.wallet_type == "user":
            wallet = self.db.query(UserWallet).filter(UserWallet.user_id == query.owner_id).first()
        elif query.wallet_type == "vendor":
            wallet = self.db.query(VendorWallet).filter(VendorWallet.vendor_id == query.owner_id).first()
        elif query.wallet_type == "rider":
            wallet = self.db.query(RiderWallet).filter(RiderWallet.rider_id == query.owner_id).first()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid wallet type")
        
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{query.wallet_type.title()} wallet not found")
        
        return wallet


# =============================================================================================================
# ORDER ITEM QUERIES
# =============================================================================================================

class GetOrderItemsQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, order_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        """Get order items with optional filtering by order_id"""
        query = self.db.query(OrderItem)
        
        if order_id:
            query = query.filter(OrderItem.order_id == order_id)
        
        order_items = query.offset(skip).limit(limit).all()
        return order_items

class GetOrderItemQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, order_item_id: int):
        """Get a single order item by ID"""
        order_item = self.db.query(OrderItem).filter(OrderItem.id == order_item_id).first()
        if not order_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                              detail=f"Order item with ID: {order_item_id} not found")
        return order_item


# =============================================================================================================
# ORDER ITEM ADDON QUERIES
# =============================================================================================================

class GetOrderItemAddonsQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, order_item_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        """Get order item addons with optional filtering by order_item_id"""
        query = self.db.query(OrderItemAddon)
        
        if order_item_id:
            query = query.filter(OrderItemAddon.order_item_id == order_item_id)
        
        addons = query.offset(skip).limit(limit).all()
        return addons

class GetOrderItemAddonQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, addon_id: int):
        """Get a single order item addon by ID"""
        addon = self.db.query(OrderItemAddon).filter(OrderItemAddon.id == addon_id).first()
        if not addon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                              detail=f"Order item addon with ID: {addon_id} not found")
        return addon


# =============================================================================================================
# ORDER TRACKING QUERIES
# =============================================================================================================

class GetOrderTrackingQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, order_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        """Get order tracking records with optional filtering by order_id"""
        query = self.db.query(OrderTracking)
        
        if order_id:
            query = query.filter(OrderTracking.order_id == order_id)
        
        # Order by timestamp for chronological tracking
        tracking_records = query.order_by(OrderTracking.timestamp).offset(skip).limit(limit).all()
        return tracking_records

class GetSingleOrderTrackingQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, tracking_id: int):
        """Get a single order tracking record by ID"""
        tracking = self.db.query(OrderTracking).filter(OrderTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                              detail=f"Order tracking with ID: {tracking_id} not found")
        return tracking

class GetLatestOrderStatusQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, order_id: int):
        """Get the latest tracking status for an order"""
        latest_tracking = (self.db.query(OrderTracking)
                          .filter(OrderTracking.order_id == order_id)
                          .order_by(OrderTracking.timestamp.desc())
                          .first())
        
        if not latest_tracking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                              detail=f"No tracking found for order ID: {order_id}")
        return latest_tracking


# =============================================================================================================
# CART ITEM QUERIES
# =============================================================================================================

class GetCartItemsQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, cart_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        """Get cart items with optional filtering by cart_id"""
        query = self.db.query(CartItem)
        
        if cart_id:
            query = query.filter(CartItem.cart_id == cart_id)
        
        cart_items = query.offset(skip).limit(limit).all()
        return cart_items

class GetCartItemQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, cart_item_id: int):
        """Get a single cart item by ID"""
        cart_item = self.db.query(CartItem).filter(CartItem.id == cart_item_id).first()
        if not cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                              detail=f"Cart item with ID: {cart_item_id} not found")
        return cart_item


# =============================================================================================================
# CART ITEM ADDON QUERIES
# =============================================================================================================

class GetCartItemAddonsQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, cart_item_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        """Get cart item addons with optional filtering by cart_item_id"""
        query = self.db.query(CartItemAddon)
        
        if cart_item_id:
            query = query.filter(CartItemAddon.cart_item_id == cart_item_id)
        
        addons = query.offset(skip).limit(limit).all()
        return addons

class GetCartItemAddonQuery:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, addon_id: int):
        """Get a single cart item addon by ID"""
        addon = self.db.query(CartItemAddon).filter(CartItemAddon.id == addon_id).first()
        if not addon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                              detail=f"Cart item addon with ID: {addon_id} not found")
        return addon

# GET WALLET TRANSACTIONS
@dataclass(frozen=True)
class GetWalletTransactionsQuery:
    wallet_type: str  # "user", "vendor", or "rider"
    owner_id: int
    limit: int = 50
    offset: int = 0

class GetWalletTransactionsQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetWalletTransactionsQuery):
        # First get the wallet
        wallet = None
        wallet_id_field = None
        
        if query.wallet_type == "user":
            wallet = self.db.query(UserWallet).filter(UserWallet.user_id == query.owner_id).first()
            wallet_id_field = WalletTransaction.user_wallet_id
        elif query.wallet_type == "vendor":
            wallet = self.db.query(VendorWallet).filter(VendorWallet.vendor_id == query.owner_id).first()
            wallet_id_field = WalletTransaction.vendor_wallet_id
        elif query.wallet_type == "rider":
            wallet = self.db.query(RiderWallet).filter(RiderWallet.rider_id == query.owner_id).first()
            wallet_id_field = WalletTransaction.rider_wallet_id
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid wallet type")
        
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{query.wallet_type.title()} wallet not found")
        
        # Get transactions for this wallet
        transactions = (
            self.db.query(WalletTransaction)
            .filter(wallet_id_field == wallet.id)
            .order_by(WalletTransaction.created_at.desc())
            .offset(query.offset)
            .limit(query.limit)
            .all()
        )
        
        return transactions

# GET SINGLE TRANSACTION
@dataclass(frozen=True)
class GetWalletTransactionQuery:
    transaction_id: int
    owner_type: str  # "user", "vendor", or "rider"
    owner_id: int

class GetWalletTransactionQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetWalletTransactionQuery):
        transaction = self.db.query(WalletTransaction).filter(WalletTransaction.id == query.transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        
        # Verify ownership
        wallet_owned = False
        if query.owner_type == "user" and transaction.user_wallet_id:
            wallet = self.db.query(UserWallet).filter(
                UserWallet.id == transaction.user_wallet_id, 
                UserWallet.user_id == query.owner_id
            ).first()
            wallet_owned = bool(wallet)
        elif query.owner_type == "vendor" and transaction.vendor_wallet_id:
            wallet = self.db.query(VendorWallet).filter(
                VendorWallet.id == transaction.vendor_wallet_id, 
                VendorWallet.vendor_id == query.owner_id
            ).first()
            wallet_owned = bool(wallet)
        elif query.owner_type == "rider" and transaction.rider_wallet_id:
            wallet = self.db.query(RiderWallet).filter(
                RiderWallet.id == transaction.rider_wallet_id, 
                RiderWallet.rider_id == query.owner_id
            ).first()
            wallet_owned = bool(wallet)
        
        if not wallet_owned:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        return transaction