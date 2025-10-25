from fastapi import HTTPException, status
from typing import Union

class ErrorHandler:
    """Centralized error handling utilities for better user experience"""
    
    @staticmethod
    def validate_positive_id(id_value: int, entity_name: str = "ID") -> None:
        """Validate that an ID is a positive integer"""
        if id_value <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {entity_name}. {entity_name} must be a positive number."
            )
    
    @staticmethod
    def validate_non_empty_string(value: str, field_name: str) -> None:
        """Validate that a string field is not empty"""
        if not value or not value.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} is required and cannot be empty."
            )
    
    @staticmethod
    def validate_email(email: str) -> None:
        """Validate email format (basic validation)"""
        if not email or "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid email address is required."
            )
    
    @staticmethod
    def not_found_error(entity_name: str, identifier: Union[int, str], additional_msg: str = "") -> HTTPException:
        """Generate a standardized not found error"""
        base_msg = f"No {entity_name.lower()} found with ID {identifier}."
        if additional_msg:
            base_msg += f" {additional_msg}"
        
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=base_msg
        )
    
    @staticmethod
    def conflict_error(entity_name: str, field_name: str, field_value: str, suggestion: str = "") -> HTTPException:
        """Generate a standardized conflict error"""
        base_msg = f"A {entity_name.lower()} with {field_name} '{field_value}' already exists."
        if suggestion:
            base_msg += f" {suggestion}"
        
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=base_msg
        )
    
    @staticmethod
    def validation_error(message: str) -> HTTPException:
        """Generate a standardized validation error"""
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    @staticmethod
    def server_error(operation: str, error_details: str = "") -> HTTPException:
        """Generate a standardized server error"""
        base_msg = f"We encountered an error while {operation}. Please try again."
        if error_details:
            base_msg += f" Error: {error_details}"
        else:
            base_msg += " If the problem persists, contact support."
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=base_msg
        )

# Common error messages
class ErrorMessages:
    """Standardized error messages for consistency"""
    
    # User-related messages
    USER_NOT_FOUND = "User account not found. Please verify the user ID is correct."
    USER_EMAIL_EXISTS = "Please use a different email address or try signing in instead."
    USER_FIREBASE_EXISTS = "This Firebase account is already linked to another user profile."
    
    # Vendor-related messages
    VENDOR_NOT_FOUND = "Vendor not found. The vendor may not exist or may have been deactivated."
    VENDOR_EMAIL_EXISTS = "Please use a different email address or try signing in instead."
    VENDOR_FIREBASE_EXISTS = "This Firebase account is already linked to another vendor profile."
    
    # Item-related messages
    ITEM_NOT_FOUND = "Menu item not found. The item may not exist or may have been removed from the menu."
    CATEGORY_NOT_FOUND = "Category not found. The category may not exist or may have been removed."
    
    # Order-related messages
    ORDER_NOT_FOUND = "Order not found. Please verify the order number is correct."
    
    # Wallet-related messages
    WALLET_NOT_FOUND = "Wallet not found. The wallet may not have been created yet."
    
    # General messages
    INVALID_COORDINATES = "Valid latitude and longitude coordinates are required."
    SEARCH_TERM_EMPTY = "Search term cannot be empty. Please provide a search query."