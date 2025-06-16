# NVIDIA's Data-FlyWheel Foundational Blueprint Orchestrated By MLRun

[MLRun](https://www.mlrun.org/) is an open-source MLOps orchestration framework that streamlines the entire machine 
learning lifecycle, from development to production. It automates data preparation, model training, and deployment as 
elastic, serverless functions, dramatically reducing time to production and engineering effort. 

This blueprint demonstrates how MLRun can orchestrate NVIDIA's NeMo Microservices platform to continuously discover and 
promote more efficient models, as shown in the original 
[NVIDIA Data Flywheel Foundational Blueprint](https://github.com/NVIDIA-AI-Blueprints/data-flywheel). MLRun provides 
automatic tracking, logging, scaling and other MLOps best practices, while reducing boilerplate code and glue logic.

> **Note**: This blueprint is a direct clone of the 
> [NVIDIA Data Flywheel Foundational Blueprint](https://github.com/NVIDIA-AI-Blueprints/data-flywheel) repository. 
> Click on the link to know more about the **Data Flywheels** and the **blueprint**, its architecture and components.

## MLRun Integration

MLRun is integrated into the original blueprint in the following order:

1. [Blueprint deployment](notebooks/data-flywheel-bp-tutorial.ipynb) now [installs](scripts/mlrun.sh) MLRun.
2. [MLRun Functions base image](deploy/mlrun/Dockerfile) is created and set as the blueprint's MLRun project default.
3. [MLRun code](src/mlrun) turning the original Blueprint tasks to modular MLRun functions.
4. [MLRun project](project.yaml) is [created](project_setup.py).
5. Blueprint is running via MLRun's Jupyter using [this notebook](mlrun-data-flywheel-tutorial.ipynb).

## Blueprint Roadmap

- [x] Using MLRun to orchestrate the original NVIDIA Data Flywheel Foundational Blueprint workflow, turning each NeMo Microservice 
      into a runnable MLRun function.
- [ ] Deploy NIMs as Nuclio serverless functions via MLRun, allowing for auto-scaling and resource management.
- [ ] Remove redundant boilerplate code and glue logic, including MongoDB requirement as all runs are stored within 
      MLRun. making the codebase cleaner and more maintainable.
- [ ] Add auto-logging capability for NeMo Evaluator and Customizer runs, logging and visualizing the jobs via MLRun.
- [ ] Generalize the blueprint to accept any dataset.

## Disclaimer

In addition to the original blueprint's disclaimer, the purpose of this Blueprint is to showcase MLRun's integration 
with NeMo Microservices and educate the community on MLOps best practices. This code is provided "as-is" as a reference 
implementation, and should not be used in production. 

## License

The MLRun-related code is licensed under the [Apache License, Version 2.0.](./LICENSE). Refer to the [NVIDIA license](./NVIDIA-LICENSE) 
for the NVIDIA AI BLUEPRINT license. For more information about NVIDIA license and additional 3rd party license data, refer to the 
[NVIDIA readme](./NVIDIA-README.md). Review all licenses before use.
