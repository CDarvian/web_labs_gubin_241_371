"""add courses and reviews tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-05-30

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'images',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('file_name', sa.String(length=100), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('md5_hash', sa.String(length=100), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=True),
        sa.Column('object_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('md5_hash'),
    )
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('short_desc', sa.Text(), nullable=False),
        sa.Column('full_desc', sa.Text(), nullable=False),
        sa.Column('rating_sum', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rating_num', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('background_image_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.ForeignKeyConstraint(['background_image_id'], ['images.id']),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('reviews')
    op.drop_table('courses')
    op.drop_table('images')
    op.drop_table('categories')
