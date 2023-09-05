# pgvector-python

[pgvector](https://github.com/pgvector/pgvector) support for Python

Supports [Django](https://github.com/django/django), [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy), [SQLModel](https://github.com/tiangolo/sqlmodel), [Psycopg 3](https://github.com/psycopg/psycopg), [Psycopg 2](https://github.com/psycopg/psycopg2), [asyncpg](https://github.com/MagicStack/asyncpg), and [Peewee](https://github.com/coleifer/peewee)

[![Build Status](https://github.com/pgvector/pgvector-python/workflows/build/badge.svg?branch=master)](https://github.com/pgvector/pgvector-python/actions)

## Installation

Run:

```sh
pip install pgvector
```

And follow the instructions for your database library:

- [Django](#django)
- [SQLAlchemy](#sqlalchemy)
- [SQLModel](#sqlmodel)
- [Psycopg 3](#psycopg-3)
- [Psycopg 2](#psycopg-2)
- [asyncpg](#asyncpg)
- [Peewee](#peewee) [unreleased]

Or check out some examples:

- [Embeddings](examples/openai_embeddings.py) with OpenAI
- [Sentence embeddings](examples/sentence_embeddings.py) with SentenceTransformers
- [Hybrid search](examples/hybrid_search.py) with SentenceTransformers
- [Image search](examples/pytorch_image_search.py) with PyTorch
- [Implicit feedback recommendations](examples/implicit_recs.py) with Implicit
- [Explicit feedback recommendations](examples/surprise_recs.py) with Surprise
- [Recommendations](examples/lightfm_recs.py) with LightFM

## Django

Create the extension

```python
from pgvector.django import VectorExtension

class Migration(migrations.Migration):
    operations = [
        VectorExtension()
    ]
```

Add a vector field

```python
from pgvector.django import VectorField

class Item(models.Model):
    embedding = VectorField(dimensions=3)
```

Insert a vector

```python
item = Item(embedding=[1, 2, 3])
item.save()
```

Get the nearest neighbors to a vector

```python
from pgvector.django import L2Distance

Item.objects.order_by(L2Distance('embedding', [3, 1, 2]))[:5]
```

Also supports `MaxInnerProduct` and `CosineDistance`

Get the distance

```python
Item.objects.annotate(distance=L2Distance('embedding', [3, 1, 2]))
```

Get items within a certain distance

```python
Item.objects.alias(distance=L2Distance('embedding', [3, 1, 2])).filter(distance__lt=5)
```

Add an approximate index

```python
from pgvector.django import IvfflatIndex

class Item(models.Model):
    class Meta:
        indexes = [
            IvfflatIndex(
                name='my_index',
                fields=['embedding'],
                lists=100,
                opclasses=['vector_l2_ops']
            )
        ]
```

Use `vector_ip_ops` for inner product and `vector_cosine_ops` for cosine distance

## SQLAlchemy

Add a vector column

```python
from pgvector.sqlalchemy import Vector

class Item(Base):
    embedding = mapped_column(Vector(3))
```

Insert a vector

```python
item = Item(embedding=[1, 2, 3])
session.add(item)
session.commit()
```

Get the nearest neighbors to a vector

```python
session.scalars(select(Item).order_by(Item.embedding.l2_distance([3, 1, 2])).limit(5))
```

Also supports `max_inner_product` and `cosine_distance`

Get the distance

```python
session.scalars(select(Item.embedding.l2_distance([3, 1, 2])))
```

Get items within a certain distance

```python
session.scalars(select(Item).filter(Item.embedding.l2_distance([3, 1, 2]) < 5))
```

Add an approximate index

```python
index = Index('my_index', Item.embedding,
    postgresql_using='ivfflat',
    postgresql_with={'lists': 100},
    postgresql_ops={'embedding': 'vector_l2_ops'}
)
index.create(engine)
```

Use `vector_ip_ops` for inner product and `vector_cosine_ops` for cosine distance

## SQLModel

Add a vector column

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column

class Item(SQLModel, table=True):
    embedding: List[float] = Field(sa_column=Column(Vector(3)))
```

Insert a vector

```python
item = Item(embedding=[1, 2, 3])
session.add(item)
session.commit()
```

Get the nearest neighbors to a vector

```python
session.exec(select(Item).order_by(Item.embedding.l2_distance([3, 1, 2])).limit(5))
```

Also supports `max_inner_product` and `cosine_distance`

## Psycopg 3

Register the vector type with your connection

```python
from pgvector.psycopg import register_vector

register_vector(conn)
```

For [async connections](https://www.psycopg.org/psycopg3/docs/advanced/async.html), use

```python
from pgvector.psycopg import register_vector_async

await register_vector_async(conn)
```

Insert a vector

```python
embedding = np.array([1, 2, 3])
conn.execute('INSERT INTO item (embedding) VALUES (%s)', (embedding,))
```

Get the nearest neighbors to a vector

```python
conn.execute('SELECT * FROM item ORDER BY embedding <-> %s LIMIT 5', (embedding,)).fetchall()
```

## Psycopg 2

Register the vector type with your connection or cursor

```python
from pgvector.psycopg2 import register_vector

register_vector(conn)
```

Insert a vector

```python
embedding = np.array([1, 2, 3])
cur.execute('INSERT INTO item (embedding) VALUES (%s)', (embedding,))
```

Get the nearest neighbors to a vector

```python
cur.execute('SELECT * FROM item ORDER BY embedding <-> %s LIMIT 5', (embedding,))
cur.fetchall()
```

## asyncpg

Register the vector type with your connection

```python
from pgvector.asyncpg import register_vector

await register_vector(conn)
```

or your pool

```python
async def init(conn):
    await register_vector(conn)

pool = await asyncpg.create_pool(..., init=init)
```

Insert a vector

```python
embedding = np.array([1, 2, 3])
await conn.execute('INSERT INTO item (embedding) VALUES ($1)', embedding)
```

Get the nearest neighbors to a vector

```python
await conn.fetch('SELECT * FROM item ORDER BY embedding <-> $1 LIMIT 5', embedding)
```

## Peewee

Add a vector column

```python
from pgvector.peewee import VectorField

class Item(BaseModel):
    embedding = VectorField(dimensions=3)
```

Insert a vector

```python
item = Item.create(embedding=[1, 2, 3])
```

Get the nearest neighbors to a vector

```python
Item.select().order_by(Item.embedding.l2_distance([3, 1, 2])).limit(5)
```

Also supports `max_inner_product` and `cosine_distance`

Get the distance

```python
Item.select(Item.embedding.l2_distance([3, 1, 2]).alias('distance'))
```

Get items within a certain distance

```python
Item.select().where(Item.embedding.l2_distance([3, 1, 2]) < 5)
```

Add an approximate index

```python
Item.add_index('embedding vector_l2_ops', using='hnsw')
```

Use `vector_ip_ops` for inner product and `vector_cosine_ops` for cosine distance

## History

View the [changelog](https://github.com/pgvector/pgvector-python/blob/master/CHANGELOG.md)

## Contributing

Everyone is encouraged to help improve this project. Here are a few ways you can help:

- [Report bugs](https://github.com/pgvector/pgvector-python/issues)
- Fix bugs and [submit pull requests](https://github.com/pgvector/pgvector-python/pulls)
- Write, clarify, or fix documentation
- Suggest or add new features

To get started with development:

```sh
git clone https://github.com/pgvector/pgvector-python.git
cd pgvector-python
pip install -r requirements.txt
createdb pgvector_python_test
pytest
```
