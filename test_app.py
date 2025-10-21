from fastapi.testclient import TestClient
import pytest
import models  
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app


SQLITE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def client():
	# create a new in-memory database and override get_db
	engine = create_engine(
		SQLITE_URL,
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	# create tables on the testing engine
	Base.metadata.create_all(bind=engine)

	# dependency override
	def override_get_db():
		db = TestingSessionLocal()
		try:
			yield db
		finally:
			db.close()

	app.dependency_overrides[get_db] = override_get_db

	with TestClient(app) as c:
		yield c

	app.dependency_overrides.pop(get_db, None)


def test_create_string_success(client):
	r = client.post("/strings/", json={"value": "racecar"})
	assert r.status_code == 201
	body = r.json()
	assert body["value"] == "racecar"
	assert "id" in body and "properties" in body


def test_create_string_empty_invalid(client):
	r = client.post("/strings/", json={"value": "   "})
	assert r.status_code == 400


def test_create_duplicate_returns_409(client):
	r1 = client.post("/strings/", json={"value": "duplicate"})
	assert r1.status_code == 201
	r2 = client.post("/strings/", json={"value": "duplicate"})
	assert r2.status_code == 409


def test_get_string_and_not_found(client):
	client.post("/strings/", json={"value": "fetchme"})
	r = client.get("/strings/fetchme")
	assert r.status_code == 200
	assert r.json()["value"] == "fetchme"

	r404 = client.get("/strings/doesnotexist")
	assert r404.status_code == 404


def test_filtering_query_params(client):
	# create dataset
	client.post("/strings/", json={"value": "racecar"})
	client.post("/strings/", json={"value": "a longer string"})
	client.post("/strings/", json={"value": "two words"})

	r = client.get("/strings", params={"is_palindrome": True})
	assert r.status_code == 200
	payload = r.json()
	assert "data" in payload and "count" in payload

	# filter by min_length
	r2 = client.get("/strings", params={"min_length": 10})
	assert r2.status_code == 200
	p2 = r2.json()
	assert p2["count"] >= 1


def test_natural_language_filter_success_and_errors(client):
	client.post("/strings/", json={"value": "racecar"})
	r = client.get("/strings/filter-by-natural-language", params={"query": "all single word palindromic strings"})
	assert r.status_code == 200
	body = r.json()
	assert "interpreted_query" in body
	parsed = body["interpreted_query"].get("parsed_filters", {})
	assert parsed.get("word_count") == 1 or parsed.get("is_palindrome") is True

	# unparsable query
	r_bad = client.get("/strings/filter-by-natural-language", params={"query": ""})
	assert r_bad.status_code == 400


def test_delete_string_flow(client):
	client.post("/strings/", json={"value": "deletethis"})
	r = client.delete("/strings/deletethis")
	assert r.status_code in (200, 204)
	# confirm gone
	r2 = client.get("/strings/deletethis")
	assert r2.status_code == 404
	


