"""empty message

Revision ID: 8252139d584f
Revises: f47178854fe9
Create Date: 2021-02-14 01:45:37.951246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8252139d584f'
down_revision = 'f47178854fe9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venues', sa.Column('genres', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venues', 'genres')
    # ### end Alembic commands ###