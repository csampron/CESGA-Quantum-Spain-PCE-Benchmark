import warnings
import sys

# Añade tu instalación local de qiskit_ibm_runtime
sys.path.append("/mnt/netapp1/Store_CESGA/home/cesga/falonso/dependencies/qiskit-ibm-runtime")

warnings.filterwarnings("ignore")

try:
    from qiskit_ibm_runtime.fake_provider.backends import (
        FakeAlgiers,
        FakeAlmadenV2,
        FakeArmonkV2,
        FakeAthensV2,
        FakeAuckland,
        FakeBelemV2,
        FakeBoeblingenV2,
        FakeBogotaV2,
        FakeBrisbane,
        FakeBrooklynV2,
        FakeBurlingtonV2,
        FakeCairoV2,
        FakeCambridgeV2,
        FakeCasablancaV2,
        FakeCusco,
        FakeEssexV2,
        FakeFez,
        FakeFractionalBackend,
        FakeGeneva,
        FakeGuadalupeV2,
        FakeHanoiV2,
        FakeJakartaV2,
        FakeJohannesburgV2,
        FakeKawasaki,
        FakeKolkataV2,
        FakeKyiv,
        FakeKyoto,
        FakeLagosV2,
        FakeLimaV2,
        FakeLondonV2,
        FakeManhattanV2,
        FakeManilaV2,
        FakeMarrakesh,
        FakeMelbourneV2,
        FakeMontrealV2,
        FakeMumbaiV2,
        FakeNairobiV2,
        FakeOsaka,
        FakeOslo,
        FakeOurenseV2,
        FakeParisV2,
        FakePeekskill,
        FakePerth,
        FakePrague,
        FakePoughkeepsieV2,
        FakeQuebec,
        FakeQuitoV2,
        FakeRochesterV2,
        FakeRomeV2,
        FakeSantiagoV2,
        FakeSherbrooke,
        FakeSingaporeV2,
        FakeSydneyV2,
        FakeTorino,
        FakeTorontoV2,
        FakeValenciaV2,
        FakeVigoV2,
        FakeWashingtonV2,
        FakeYorktownV2,
    )
except ImportError as e:
    print("Error importando fake backends:", e)
    sys.exit(1)


# Lista de todas las clases de backends
fake_backend_classes = [
    FakeAlgiers, FakeAlmadenV2, FakeArmonkV2, FakeAthensV2, FakeAuckland,
    FakeBelemV2, FakeBoeblingenV2, FakeBogotaV2, FakeBrisbane,
    FakeBrooklynV2, FakeBurlingtonV2, FakeCairoV2, FakeCambridgeV2,
    FakeCasablancaV2, FakeCusco, FakeEssexV2, FakeFez,
    FakeFractionalBackend, FakeGeneva, FakeGuadalupeV2, FakeHanoiV2,
    FakeJakartaV2, FakeJohannesburgV2, FakeKawasaki, FakeKolkataV2,
    FakeKyiv, FakeKyoto, FakeLagosV2, FakeLimaV2, FakeLondonV2,
    FakeManhattanV2, FakeManilaV2, FakeMarrakesh, FakeMelbourneV2,
    FakeMontrealV2, FakeMumbaiV2, FakeNairobiV2, FakeOsaka, FakeOslo,
    FakeOurenseV2, FakeParisV2, FakePeekskill, FakePerth, FakePrague,
    FakePoughkeepsieV2, FakeQuebec, FakeQuitoV2, FakeRochesterV2,
    FakeRomeV2, FakeSantiagoV2, FakeSherbrooke, FakeSingaporeV2,
    FakeSydneyV2, FakeTorino, FakeTorontoV2, FakeValenciaV2,
    FakeVigoV2, FakeWashingtonV2, FakeYorktownV2
]

print("\nFake backends con MÁS de 25 qubits:\n")

for backend_class in fake_backend_classes:
    try:
        backend = backend_class()
        num_qubits = backend.num_qubits

        if 60 > num_qubits > 25:
            config = backend.configuration()
            print(f"Nombre: {backend.name}")
            print(f"Qubits: {num_qubits}")
            print(f"Puertas nativas: {config.basis_gates}")
            #print(f"Conectividad (coupling_map): {config.coupling_map}")
            print("-" * 60)

    except Exception as e:
        print(f"No se pudo inicializar {backend_class.__name__}: {e}")
