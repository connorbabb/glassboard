# alembic/versions/<some_id>_create_users_table.py
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "xxxx_users_table"
down_revision = None  # or whatever your previous migration is
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String, unique=True, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False)
    )

def downgrade():
    op.drop_table("users")
