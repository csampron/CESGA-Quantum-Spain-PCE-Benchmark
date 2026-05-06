### ===================================================== ###
###   Script de carga de módulos para CUNQA HPC           ###
### ===================================================== ###
###
### Este script se encarga de cargar todos los módulos
### necesarios para ejecutar los proyectos en el entorno
### de CUNQA. Al ejecutar:
###
###     source init_CUNQA.sh
###
### se cargarán los compiladores, librerías, frameworks
### y herramientas de Python necesarias para el desarrollo
### y ejecución de código en el cluster.
###

# Limpiar módulos previamente cargados
module purge

# Cargar módulos principales de compiladores, MPI y librerías
module load qmio/hpc gcc/12.3.0 hpcx-ompi flexiblas/3.3.0 boost cmake/3.27.6 gcccore/12.3.0 nlohmann_json/3.11.3 ninja/1.9.0 pybind11/2.13.6-python-3.11.9 qiskit/1.2.4-python-3.11.9

# Cargar módulos adicionales de Python para grafos y visualización
module load qmio/hpc gcc/12.3.0 networkx/3.3-python-3.11.9
module load qmio/hpc gcccore/12.3.0 matplotlib/3.6.3-python-3.11.9
