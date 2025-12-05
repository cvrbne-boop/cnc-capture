"""orders: add customers, orders, order_items

Revision ID: 0002_orders
Revises: 0001_create_tables
Create Date: 2025-12-03 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_orders'
down_revision = '0001_create_tables'
branch_labels = None
depends_on = None


def upgrade():
    # customers
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
    )
    op.create_index('ix_customers_id', 'customers', ['id'])

    # orders
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id')),
        sa.Column('order_number', sa.String(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_orders_id', 'orders', ['id'])

    # order_items
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id')),
        sa.Column('drawing_number', sa.String(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
    )
    op.create_index('ix_order_items_id', 'order_items', ['id'])


def downgrade():
    op.drop_index('ix_order_items_id', table_name='order_items')
    op.drop_table('order_items')
    op.drop_index('ix_orders_id', table_name='orders')
    op.drop_table('orders')
    op.drop_index('ix_customers_id', table_name='customers')
    op.drop_table('customers')
