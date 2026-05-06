import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import inspect
import qiskit.providers.fake_provider as fake_provider
from qiskit.providers.fake_provider import FakeBackend

print("Fake backends (Pulse o QASM) con más de 20 qubits:\n")

# Obtener todas las clases que hereden de FakeBackend
fake_backends = [
    cls for name, cls in inspect.getmembers(fake_provider, inspect.isclass)
    if issubclass(cls, FakeBackend) and cls is not FakeBackend
]

for backend_class in fake_backends:
    try:
        backend = backend_class()
        # Intentar obtener número de qubits
        try:
            num_qubits = backend.num_qubits
        except AttributeError:
            num_qubits = backend.configuration().n_qubits

        if num_qubits > 20:
            config = backend.configuration()

            # Determinar tipo: Pulse o QASM
            if 'pulse' in config.backend_name.lower():
                tipo = 'Pulse'
            else:
                tipo = 'QASM'

            print(f"Nombre: {backend.name()}")
            print(f"Número de qubits: {num_qubits}")
            print(f"Tipo: {tipo}")
            print(f"Puertas nativas (basis_gates): {config.basis_gates}")
            if hasattr(config, 'coupling_map'):
                print(f"Acoplamientos (coupling_map): {config.coupling_map}\n")

    except Exception:
        # Ignorar backends que no se puedan inicializar
        continue
