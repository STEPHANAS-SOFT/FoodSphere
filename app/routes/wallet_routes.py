from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..services.commands import (
    FundUserWalletCommand, FundUserWalletHandler,
    WithdrawFromWalletCommand, WithdrawFromWalletHandler,
    TransferBetweenWalletsCommand, TransferBetweenWalletsHandler,
    ProcessOrderPaymentCommand, ProcessOrderPaymentHandler,
    SetTransactionPinCommand, SetTransactionPinHandler
)
from ..services.queries import (
    GetWalletBalanceQuery, GetWalletBalanceQueryHandler,
    GetWalletTransactionsQuery, GetWalletTransactionsQueryHandler,
    GetWalletTransactionQuery, GetWalletTransactionQueryHandler
)
from ..schemas import (
    WalletFundRequest, WalletWithdrawRequest, WalletTransferRequest,
    SetTransactionPinRequest, UserWalletResponse, VendorWalletResponse,
    RiderWalletResponse, WalletTransactionResponse, WalletBalanceResponse
)

router = APIRouter(prefix="/api/wallet", tags=["Wallets"], dependencies=[Depends(verify_api_key)])

# ===== User Wallet Routes =====

@router.get("/user/{user_id}/balance", response_model=UserWalletResponse)
def get_user_wallet_balance(user_id: int, db: Session = Depends(get_db)):
    """Get user wallet balance and details"""
    query = GetWalletBalanceQuery(wallet_type="user", owner_id=user_id)
    handler = GetWalletBalanceQueryHandler(db)
    return handler.handle(query)

@router.post("/user/{user_id}/fund", response_model=WalletTransactionResponse)
def fund_user_wallet(user_id: int, request: WalletFundRequest, db: Session = Depends(get_db)):
    """Fund a user's wallet"""
    command = FundUserWalletCommand(
        user_id=user_id,
        amount=request.amount,
        description=request.description,
        payment_method=request.payment_method
    )
    handler = FundUserWalletHandler(db)
    return handler.handle(command)

@router.post("/user/{user_id}/withdraw", response_model=WalletTransactionResponse)
def withdraw_from_user_wallet(user_id: int, request: WalletWithdrawRequest, db: Session = Depends(get_db)):
    """Withdraw from a user's wallet"""
    command = WithdrawFromWalletCommand(
        wallet_type="user",
        owner_id=user_id,
        amount=request.amount,
        description=request.description,
        withdrawal_method=request.withdrawal_method,
        account_details=request.account_details
    )
    handler = WithdrawFromWalletHandler(db)
    return handler.handle(command)

@router.get("/user/{user_id}/transactions", response_model=List[WalletTransactionResponse])
def get_user_wallet_transactions(
    user_id: int, 
    limit: int = 50, 
    offset: int = 0, 
    db: Session = Depends(get_db), 
):
    """Get user wallet transaction history"""
    query = GetWalletTransactionsQuery(wallet_type="user", owner_id=user_id, limit=limit, offset=offset)
    handler = GetWalletTransactionsQueryHandler(db)
    return handler.handle(query)

@router.post("/user/{user_id}/set-pin")
def set_user_transaction_pin(user_id: int, request: SetTransactionPinRequest, db: Session = Depends(get_db)):
    """Set transaction PIN for user wallet"""
    if request.transaction_pin != request.confirm_pin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PINs do not match")
    
    command = SetTransactionPinCommand(user_id=user_id, transaction_pin=request.transaction_pin)
    handler = SetTransactionPinHandler(db)
    return handler.handle(command)

# ===== Vendor Wallet Routes =====

@router.get("/vendor/{vendor_id}/balance", response_model=VendorWalletResponse)
def get_vendor_wallet_balance(vendor_id: int, db: Session = Depends(get_db)):
    """Get vendor wallet balance and details"""
    query = GetWalletBalanceQuery(wallet_type="vendor", owner_id=vendor_id)
    handler = GetWalletBalanceQueryHandler(db)
    return handler.handle(query)

@router.post("/vendor/{vendor_id}/withdraw", response_model=WalletTransactionResponse)
def withdraw_from_vendor_wallet(vendor_id: int, request: WalletWithdrawRequest, db: Session = Depends(get_db)):
    """Withdraw earnings from vendor wallet"""
    command = WithdrawFromWalletCommand(
        wallet_type="vendor",
        owner_id=vendor_id,
        amount=request.amount,
        description=request.description,
        withdrawal_method=request.withdrawal_method,
        account_details=request.account_details
    )
    handler = WithdrawFromWalletHandler(db)
    return handler.handle(command)

@router.get("/vendor/{vendor_id}/transactions", response_model=List[WalletTransactionResponse])
def get_vendor_wallet_transactions(
    vendor_id: int, 
    limit: int = 50, 
    offset: int = 0, 
    db: Session = Depends(get_db), 
):
    """Get vendor wallet transaction history"""
    query = GetWalletTransactionsQuery(wallet_type="vendor", owner_id=vendor_id, limit=limit, offset=offset)
    handler = GetWalletTransactionsQueryHandler(db)
    return handler.handle(query)

# ===== Rider Wallet Routes =====

@router.get("/rider/{rider_id}/balance", response_model=RiderWalletResponse)
def get_rider_wallet_balance(rider_id: int, db: Session = Depends(get_db)):
    """Get rider wallet balance and details"""
    query = GetWalletBalanceQuery(wallet_type="rider", owner_id=rider_id)
    handler = GetWalletBalanceQueryHandler(db)
    return handler.handle(query)

@router.post("/rider/{rider_id}/withdraw", response_model=WalletTransactionResponse)
def withdraw_from_rider_wallet(rider_id: int, request: WalletWithdrawRequest, db: Session = Depends(get_db)):
    """Withdraw earnings from rider wallet"""
    command = WithdrawFromWalletCommand(
        wallet_type="rider",
        owner_id=rider_id,
        amount=request.amount,
        description=request.description,
        withdrawal_method=request.withdrawal_method,
        account_details=request.account_details
    )
    handler = WithdrawFromWalletHandler(db)
    return handler.handle(command)

@router.get("/rider/{rider_id}/transactions", response_model=List[WalletTransactionResponse])
def get_rider_wallet_transactions(
    rider_id: int, 
    limit: int = 50, 
    offset: int = 0, 
    db: Session = Depends(get_db)
):
    """Get rider wallet transaction history"""
    query = GetWalletTransactionsQuery(wallet_type="rider", owner_id=rider_id, limit=limit, offset=offset)
    handler = GetWalletTransactionsQueryHandler(db)
    return handler.handle(query)

# ===== Transfer Routes =====

@router.post("/transfer", response_model=dict)
def transfer_between_wallets(request: WalletTransferRequest, db: Session = Depends(get_db)):
    """Transfer money between wallets"""
    # Note: In a real application, you'd need to verify the sender's identity and PIN
    command = TransferBetweenWalletsCommand(
        sender_type="user",  # This would come from authentication context
        sender_id=1,  # This would come from authentication context
        recipient_type=request.recipient_type,
        recipient_id=request.recipient_id,
        amount=request.amount,
        description=request.description
    )
    handler = TransferBetweenWalletsHandler(db)
    return handler.handle(command)

# ===== Transaction Details =====

@router.get("/transaction/{transaction_id}", response_model=WalletTransactionResponse)
def get_transaction_details(
    transaction_id: int, 
    owner_type: str, 
    owner_id: int, 
    db: Session = Depends(get_db)
):
    """Get details of a specific transaction"""
    query = GetWalletTransactionQuery(
        transaction_id=transaction_id,
        owner_type=owner_type,
        owner_id=owner_id
    )
    handler = GetWalletTransactionQueryHandler(db)
    return handler.handle(query)

# ===== Payment Processing (Internal) =====

@router.post("/internal/process-payment", response_model=WalletTransactionResponse)
def process_order_payment(
    order_id: int, 
    user_id: int, 
    amount: float, 
    db: Session = Depends(get_db)
):
    """Process payment for an order (internal use)"""
    command = ProcessOrderPaymentCommand(
        order_id=order_id,
        user_id=user_id,
        amount=amount
    )
    handler = ProcessOrderPaymentHandler(db)
    return handler.handle(command)