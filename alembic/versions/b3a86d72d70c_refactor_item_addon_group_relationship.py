"""refactor_item_addon_group_relationship

Revision ID: b3a86d72d70c
Revises: 9efe7ce1340a
Create Date: 2025-11-08 15:50:27.750137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3a86d72d70c'
down_revision: Union[str, Sequence[str], None] = '9efe7ce1340a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Move item_id from ItemAddonGroup to Item as addon_group_id."""
    # Add addon_group_id column to items table
    op.add_column('items', sa.Column('addon_group_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_items_addon_group_id',
        'items',
        'item_addon_groups',
        ['addon_group_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Migrate data: For each item_addon_group, set the addon_group_id on the item
    op.execute("""
        UPDATE items
        SET addon_group_id = iag.id
        FROM item_addon_groups iag
        WHERE iag.item_id = items.id
    """)
    
    # Drop the foreign key constraint from item_addon_groups
    op.drop_constraint('item_addon_groups_item_id_fkey', 'item_addon_groups', type_='foreignkey')
    
    # Drop the item_id column from item_addon_groups
    op.drop_column('item_addon_groups', 'item_id')


def downgrade() -> None:
    """Downgrade schema: Move addon_group_id from Item back to ItemAddonGroup as item_id."""
    # Add item_id column back to item_addon_groups table
    op.add_column('item_addon_groups', sa.Column('item_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'item_addon_groups_item_id_fkey',
        'item_addon_groups',
        'items',
        ['item_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Migrate data back: For each item with addon_group_id, set item_id on the addon_group
    op.execute("""
        UPDATE item_addon_groups
        SET item_id = i.id
        FROM items i
        WHERE i.addon_group_id = item_addon_groups.id
    """)
    
    # Drop the foreign key constraint from items
    op.drop_constraint('fk_items_addon_group_id', 'items', type_='foreignkey')
    
    # Drop the addon_group_id column from items
    op.drop_column('items', 'addon_group_id')
    
    # Make item_id NOT NULL again
    op.alter_column('item_addon_groups', 'item_id', nullable=False)
