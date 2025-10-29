from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..models import (
    Order, User, UserWallet, VendorWallet, RiderWallet,
    WalletTransaction, WalletTransactionType, WalletTransactionStatus
)


router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)


class PaymentMethod(BaseModel):
    id: str
    type: str  # "credit_card", "debit_card", "wallet", "bank_account"
    last_four: Optional[str] = None
    brand: Optional[str] = None  # "visa", "mastercard", etc.
    is_default: bool = False
    expires_at: Optional[str] = None


class PaymentRequest(BaseModel):
    order_id: int
    payment_method_id: str
    payment_type: str  # "credit_card", "wallet", "cash_on_delivery"
    amount: float
    currency: str = "USD"
    save_payment_method: bool = False


class PaymentResponse(BaseModel):
    payment_id: str
    status: str  # "pending", "processing", "completed", "failed"
    amount: float
    currency: str
    payment_method: str
    transaction_fee: float
    created_at: datetime
    order_id: int


class RefundRequest(BaseModel):
    reason: str
    amount: Optional[float] = None  # Partial refund if specified
    refund_to_wallet: bool = True


class RefundResponse(BaseModel):
    refund_id: str
    status: str
    amount: float
    original_payment_id: str
    processing_time: str
    refund_method: str


@router.post("/process", response_model=PaymentResponse)
async def process_payment(
    payment_request: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Process payment for an order"""
    
    # Verify order exists
    order = db.query(Order).filter(Order.id == payment_request.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Validate payment amount matches order total
    order_total = float(order.total_amount)
    if abs(payment_request.amount - order_total) > 0.01:  # Allow small floating point differences
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount {payment_request.amount} doesn't match order total {order_total}"
        )
    
    payment_id = str(uuid4())
    transaction_fee = 0.0
    
    try:
        if payment_request.payment_type == "wallet":
            # Process wallet payment
            user_wallet = db.query(UserWallet).filter(UserWallet.user_id == order.user_id).first()
            
            if not user_wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User wallet not found"
                )
            
            if float(user_wallet.balance) < payment_request.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient wallet balance"
                )
            
            # Deduct from user wallet
            user_wallet.balance -= Decimal(str(payment_request.amount))
            
            # Create wallet transaction
            transaction = WalletTransaction(
                wallet_type="user",
                wallet_id=user_wallet.id,
                transaction_type=WalletTransactionType.PAYMENT,
                amount=Decimal(str(payment_request.amount)),
                status=WalletTransactionStatus.COMPLETED,
                description=f"Payment for order #{order.id}",
                reference_id=payment_id
            )
            db.add(transaction)
            
            # Add to vendor wallet (minus platform commission)
            vendor_wallet = db.query(VendorWallet).filter(VendorWallet.vendor_id == order.vendor_id).first()
            if vendor_wallet:
                platform_commission = payment_request.amount * 0.05  # 5% commission
                vendor_amount = payment_request.amount - platform_commission
                
                vendor_wallet.balance += Decimal(str(vendor_amount))
                
                vendor_transaction = WalletTransaction(
                    wallet_type="vendor",
                    wallet_id=vendor_wallet.id,
                    transaction_type=WalletTransactionType.DEPOSIT,
                    amount=Decimal(str(vendor_amount)),
                    status=WalletTransactionStatus.COMPLETED,
                    description=f"Payment for order #{order.id} (after commission)",
                    reference_id=payment_id
                )
                db.add(vendor_transaction)
            
            payment_status = "completed"
        
        elif payment_request.payment_type in ["credit_card", "debit_card"]:
            # Simulate card payment processing
            transaction_fee = payment_request.amount * 0.029  # 2.9% processing fee
            
            # In real implementation, you'd integrate with Stripe, PayPal, etc.
            # For simulation, we'll assume success
            payment_status = "completed"
            
            # Still need to credit vendor wallet
            vendor_wallet = db.query(VendorWallet).filter(VendorWallet.vendor_id == order.vendor_id).first()
            if vendor_wallet:
                platform_commission = payment_request.amount * 0.05
                processing_cost = transaction_fee
                vendor_amount = payment_request.amount - platform_commission - processing_cost
                
                vendor_wallet.balance += Decimal(str(vendor_amount))
                
                vendor_transaction = WalletTransaction(
                    wallet_type="vendor",
                    wallet_id=vendor_wallet.id,
                    transaction_type=WalletTransactionType.DEPOSIT,
                    amount=Decimal(str(vendor_amount)),
                    status=WalletTransactionStatus.COMPLETED,
                    description=f"Card payment for order #{order.id}",
                    reference_id=payment_id
                )
                db.add(vendor_transaction)
        
        elif payment_request.payment_type == "cash_on_delivery":
            payment_status = "pending"  # Will be completed when delivered
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported payment type"
            )
        
        # Update order payment status
        order.payment_status = payment_status
        order.payment_method = payment_request.payment_type
        order.updated_at = datetime.utcnow()
        
        db.commit()
        
        return PaymentResponse(
            payment_id=payment_id,
            status=payment_status,
            amount=payment_request.amount,
            currency=payment_request.currency,
            payment_method=payment_request.payment_type,
            transaction_fee=transaction_fee,
            created_at=datetime.utcnow(),
            order_id=payment_request.order_id
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment processing failed: {str(e)}"
        )


@router.get("/{payment_id}/status")
async def check_payment_status(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Check the status of a payment"""
    
    # Find transaction by reference_id
    transaction = db.query(WalletTransaction).filter(
        WalletTransaction.reference_id == payment_id
    ).first()
    
    if not transaction:
        # In real implementation, you'd also check external payment processors
        return {
            "payment_id": payment_id,
            "status": "not_found",
            "message": "Payment not found"
        }
    
    return {
        "payment_id": payment_id,
        "status": transaction.status.value,
        "amount": float(transaction.amount),
        "created_at": transaction.created_at,
        "description": transaction.description
    }


@router.post("/{payment_id}/refund", response_model=RefundResponse)
async def process_refund(
    payment_id: str,
    refund_request: RefundRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Process a refund for a payment"""
    
    # Find original transaction
    original_transaction = db.query(WalletTransaction).filter(
        WalletTransaction.reference_id == payment_id,
        WalletTransaction.transaction_type == WalletTransactionType.PAYMENT
    ).first()
    
    if not original_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original payment not found"
        )
    
    # Determine refund amount
    refund_amount = refund_request.amount or float(original_transaction.amount)
    original_amount = float(original_transaction.amount)
    
    if refund_amount > original_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount cannot exceed original payment"
        )
    
    refund_id = str(uuid4())
    
    try:
        if refund_request.refund_to_wallet:
            # Refund to user wallet
            if original_transaction.wallet_type == "user":
                user_wallet = db.query(UserWallet).filter(
                    UserWallet.id == original_transaction.wallet_id
                ).first()
                
                if user_wallet:
                    user_wallet.balance += Decimal(str(refund_amount))
                    
                    refund_transaction = WalletTransaction(
                        wallet_type="user",
                        wallet_id=user_wallet.id,
                        transaction_type=WalletTransactionType.REFUND,
                        amount=Decimal(str(refund_amount)),
                        status=WalletTransactionStatus.COMPLETED,
                        description=f"Refund for payment {payment_id}: {refund_request.reason}",
                        reference_id=refund_id
                    )
                    db.add(refund_transaction)
            
            refund_method = "wallet"
            processing_time = "instant"
        
        else:
            # Refund to original payment method
            # In real implementation, you'd call external payment processor APIs
            refund_method = "original_payment_method"
            processing_time = "3-5 business days"
        
        # Deduct from vendor wallet if applicable
        # (This is simplified - in reality you'd have more complex business logic)
        
        db.commit()
        
        return RefundResponse(
            refund_id=refund_id,
            status="completed" if refund_request.refund_to_wallet else "processing",
            amount=refund_amount,
            original_payment_id=payment_id,
            processing_time=processing_time,
            refund_method=refund_method
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund processing failed: {str(e)}"
        )


@router.get("/users/{user_id}/payment-methods", response_model=List[PaymentMethod])
async def get_saved_payment_methods(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get user's saved payment methods"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # In a real implementation, you'd fetch from payment processor or database
    # For now, we'll return mock data
    payment_methods = [
        PaymentMethod(
            id="pm_1234567890",
            type="credit_card",
            last_four="4242",
            brand="visa",
            is_default=True,
            expires_at="12/25"
        ),
        PaymentMethod(
            id="pm_0987654321",
            type="debit_card",
            last_four="1234",
            brand="mastercard",
            is_default=False,
            expires_at="06/26"
        ),
        PaymentMethod(
            id="wallet",
            type="wallet",
            is_default=False
        )
    ]
    
    return payment_methods


@router.post("/users/{user_id}/payment-methods")
async def save_payment_method(
    user_id: int,
    payment_method_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Save a new payment method for user"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # In a real implementation, you'd:
    # 1. Validate card details with payment processor
    # 2. Tokenize sensitive information
    # 3. Store secure tokens in database
    # 4. Return safe representation
    
    # For simulation, we'll return a success response
    payment_method_id = str(uuid4())
    
    return {
        "message": "Payment method saved successfully",
        "payment_method_id": payment_method_id,
        "type": payment_method_data.get("type", "credit_card"),
        "last_four": payment_method_data.get("card_number", "0000")[-4:] if payment_method_data.get("card_number") else None,
        "is_default": payment_method_data.get("is_default", False)
    }


@router.delete("/users/{user_id}/payment-methods/{payment_method_id}")
async def delete_payment_method(
    user_id: int,
    payment_method_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Delete a saved payment method"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # In real implementation, you'd remove from payment processor and database
    
    return {
        "message": "Payment method deleted successfully",
        "payment_method_id": payment_method_id
    }


@router.get("/transactions/{transaction_id}")
async def get_transaction_details(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get detailed transaction information"""
    
    transaction = db.query(WalletTransaction).filter(
        WalletTransaction.reference_id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return {
        "transaction_id": transaction_id,
        "type": transaction.transaction_type.value,
        "amount": float(transaction.amount),
        "status": transaction.status.value,
        "description": transaction.description,
        "created_at": transaction.created_at,
        "wallet_type": transaction.wallet_type,
        "fees": {
            "processing_fee": 0.0,  # Would calculate based on payment method
            "platform_fee": float(transaction.amount) * 0.05 if transaction.transaction_type == WalletTransactionType.PAYMENT else 0.0
        }
    }


@router.post("/verify-payment-method")
async def verify_payment_method(
    payment_method_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Verify payment method without saving it"""
    
    # In real implementation, you'd validate with payment processor
    # For simulation, we'll do basic validation
    
    card_number = payment_method_data.get("card_number", "")
    expiry = payment_method_data.get("expiry", "")
    cvv = payment_method_data.get("cvv", "")
    
    if not card_number or len(card_number.replace(" ", "")) < 13:
        return {"valid": False, "error": "Invalid card number"}
    
    if not expiry or len(expiry) != 5:  # MM/YY format
        return {"valid": False, "error": "Invalid expiry date"}
    
    if not cvv or len(cvv) < 3:
        return {"valid": False, "error": "Invalid CVV"}
    
    # Determine card brand
    card_brand = "unknown"
    if card_number.startswith("4"):
        card_brand = "visa"
    elif card_number.startswith(("51", "52", "53", "54", "55")):
        card_brand = "mastercard"
    elif card_number.startswith("34") or card_number.startswith("37"):
        card_brand = "amex"
    
    return {
        "valid": True,
        "card_brand": card_brand,
        "last_four": card_number[-4:],
        "processing_fees": {
            "percentage": 2.9,
            "fixed_fee": 0.30
        }
    }