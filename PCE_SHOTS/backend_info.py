import inspect
import qiskit.providers.fake_provider as fake_provider

# Listar todos los nombres de clases FakeBackend disponibles
fake_backends = [
    name for name, cls in inspect.getmembers(fake_provider, inspect.isclass)
    if issubclass(cls, fake_provider.FakeBackend) and cls is not fake_provider.FakeBackend
]

print("Todos los fake backends disponibles en esta instalación:")
for name in fake_backends:
    print("-", name)
