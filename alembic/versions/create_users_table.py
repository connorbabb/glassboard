# alembic/versions/<some_id>_create_users_table.py
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a7afee95e6b5"
down_revision = "b8bd4eb41fec"
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
