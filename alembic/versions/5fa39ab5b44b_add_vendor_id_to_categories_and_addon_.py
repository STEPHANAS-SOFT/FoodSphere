"""add_vendor_id_to_categories_and_addon_groups

Revision ID: 5fa39ab5b44b
Revises: b3a86d72d70c
Create Date: 2025-11-08 16:04:18.965911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fa39ab5b44b'
down_revision: Union[str, Sequence[str], None] = 'b3a86d72d70c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add vendor_id to item_categories and item_addon_groups."""
    # Add vendor_id column to item_categories table (nullable initially)
    op.add_column('item_categories', sa.Column('vendor_id', sa.Integer(), nullable=True))
    
    # Add vendor_id column to item_addon_groups table (nullable initially)
    op.add_column('item_addon_groups', sa.Column('vendor_id', sa.Integer(), nullable=True))
    
    # For existing data, set vendor_id based on items that reference these categories/addon_groups
    # Set vendor_id for categories based on items
    op.execute("""
        UPDATE item_categories
        SET vendor_id = (
            SELECT vendor_id 
            FROM items 
            WHERE items.category_id = item_categories.id 
            LIMIT 1
        )
        WHERE vendor_id IS NULL
    """)
    
    # Set vendor_id for addon_groups based on items that use them
    op.execute("""
        UPDATE item_addon_groups
        SET vendor_id = (
            SELECT vendor_id 
            FROM items 
            WHERE items.addon_group_id = item_addon_groups.id 
            LIMIT 1
        )
        WHERE vendor_id IS NULL
    """)
    
    # For any remaining NULL values (orphaned records), delete them or set to first vendor
    # Option: Delete orphaned records
    op.execute("DELETE FROM item_categories WHERE vendor_id IS NULL")
    op.execute("DELETE FROM item_addon_groups WHERE vendor_id IS NULL")
    
    # Make vendor_id NOT NULL after data migration
    op.alter_column('item_categories', 'vendor_id', nullable=False)
    op.alter_column('item_addon_groups', 'vendor_id', nullable=False)
    
    # Create foreign key constraints
    op.create_foreign_key(
        'fk_item_categories_vendor_id',
        'item_categories',
        'vendors',
        ['vendor_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_item_addon_groups_vendor_id',
        'item_addon_groups',
        'vendors',
        ['vendor_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema: Remove vendor_id from item_categories and item_addon_groups."""
    # Drop foreign key constraints
    op.drop_constraint('fk_item_categories_vendor_id', 'item_categories', type_='foreignkey')
    op.drop_constraint('fk_item_addon_groups_vendor_id', 'item_addon_groups', type_='foreignkey')
    
    # Drop vendor_id columns
    op.drop_column('item_categories', 'vendor_id')
    op.drop_column('item_addon_groups', 'vendor_id')
