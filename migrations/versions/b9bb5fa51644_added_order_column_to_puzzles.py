"""Added order column to puzzles

Revision ID: b9bb5fa51644
Revises: b72ebca069c9
Create Date: 2023-09-17 12:11:37.437260

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9bb5fa51644'
down_revision = 'b72ebca069c9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('puzzle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('puzzle', schema=None) as batch_op:
        batch_op.drop_column('order')

    # ### end Alembic commands ###
