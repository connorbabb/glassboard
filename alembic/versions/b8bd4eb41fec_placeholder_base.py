# alembic/versions/b8bd4eb41fec_placeholder_base.py

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b8bd4eb41fec"
down_revision = None # <--- It has no history before it
branch_labels = None
depends_on = None

def upgrade():
    # We assume this table already exists in the live database, 
    # so we don't need to run actual CREATE TABLE statements.
    pass

def downgrade():
    pass