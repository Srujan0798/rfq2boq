"""Neo4j graph knowledge base for RFQ2BOQ."""

import os
from dataclasses import dataclass

try:
    from neo4j import GraphDatabase

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


@dataclass
class Material:
    name: str
    category: str = ""
    density: float = 0.0
    aliases: list[str] | None = None
    common_units: list[str] | None = None
    standards: list[str] | None = None
    grades: list[str] | None = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.common_units is None:
            self.common_units = []
        if self.standards is None:
            self.standards = []
        if self.grades is None:
            self.grades = []


@dataclass
class Standard:
    code: str
    body: str = ""
    year: int = 0
    title: str = ""
    aliases: list[str] | None = None
    equivalents: list[str] | None = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.equivalents is None:
            self.equivalents = []


class GraphOntology:
    """Neo4j-backed knowledge graph for construction ontology."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        if NEO4J_AVAILABLE:
            try:
                driver = GraphDatabase.driver(uri, auth=(user, password))
                try:
                    driver.verify_connectivity()
                    self.driver = driver
                except Exception:
                    driver.close()
            except Exception:
                pass

    @property
    def is_available(self) -> bool:
        return self.driver is not None

    def close(self):
        if self.driver:
            self.driver.close()

    def lookup_material(self, name: str) -> Material | None:
        """Look up material with related standards, units, grades."""
        if not self.driver:
            return None
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (m:Material {name: $name})
                OPTIONAL MATCH (m)-[:COMPLIES_WITH]->(s:Standard)
                OPTIONAL MATCH (m)-[:MEASURED_IN]->(u:Unit)
                OPTIONAL MATCH (m)-[:HAS_GRADE]->(g:Grade)
                RETURN m, collect(DISTINCT s.code) as standards,
                       collect(DISTINCT u.symbol) as units,
                       collect(DISTINCT g.code) as grades
                """,
                name=name,
            )
            record = result.single()
            if record:
                m = record["m"]
                return Material(
                    name=m["name"],
                    category=m.get("category", ""),
                    density=m.get("density", 0.0),
                    aliases=m.get("aliases", []),
                    common_units=record["units"],
                    standards=record["standards"],
                    grades=record["grades"],
                )
        return None

    def lookup_standard(self, code: str) -> Standard | None:
        """Look up standard with equivalents and applicable materials."""
        if not self.driver:
            return None
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Standard {code: $code})
                OPTIONAL MATCH (s)-[:EQUIVALENT_TO]->(eq:Standard)
                OPTIONAL MATCH (m:Material)-[:COMPLIES_WITH]->(s)
                RETURN s, collect(DISTINCT eq.code) as equivalents,
                       collect(DISTINCT m.name) as materials
                """,
                code=code,
            )
            record = result.single()
            if record:
                s = record["s"]
                return Standard(
                    code=s["code"],
                    body=s.get("body", ""),
                    year=s.get("year", 0),
                    title=s.get("title", ""),
                    aliases=s.get("aliases", []),
                    equivalents=record["equivalents"],
                )
        return None

    def find_compatible_standards(self, material: str) -> list[str]:
        """Find standards compatible with a material."""
        if not self.driver:
            return []
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (m:Material {name: $material})-[:COMPLIES_WITH]->(s:Standard)
                RETURN s.code as code
                """,
                material=material,
            )
            return [r["code"] for r in result]

    def convert_unit(self, value: float, from_unit: str, to_unit: str) -> float | None:
        """Convert value between units using graph knowledge."""
        if not self.driver:
            return None
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u1:Unit {symbol: $from})-[r:CONVERTS_TO]->(u2:Unit {symbol: $to})
                RETURN r.factor as factor
                """,
                from_=from_unit,
                to=to_unit,
            )
            record = result.single()
            if record:
                factor = float(record["factor"])
                return value * factor
        return None

    def find_equivalent_standard(self, code: str, region: str) -> Standard | None:
        """Find equivalent standard for a region."""
        if not self.driver:
            return None
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s1:Standard {code: $code})-[:EQUIVALENT_TO {region: $region}]->(s2:Standard)
                RETURN s2
                """,
                code=code,
                region=region,
            )
            record = result.single()
            if record:
                s = record["s2"]
                return Standard(
                    code=s["code"],
                    body=s.get("body", ""),
                    year=s.get("year", 0),
                    title=s.get("title", ""),
                )
        return None

    def multi_hop_query(self, start_node: str, max_depth: int = 3) -> list[list[dict]]:
        """Perform multi-hop traversal from start node."""
        if not self.driver:
            return []
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH path = (start {{name: $start}})-[*1..{max_depth}]->(end)
                RETURN path
                """,
                start=start_node,
            )
            paths: list[list[dict]] = []
            for r in result:
                path = r["path"]
                nodes = [dict(n) for n in path.nodes]
                paths.append(nodes)
            return paths


def get_graph_ontology() -> GraphOntology:
    """Get graph ontology from environment or default."""
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "rfq2boq_dev")
    return GraphOntology(uri=uri, user=user, password=password)
