DOCKER_SERVER="${DOCKER_SERVER:-}"
DOCKER_USERNAME="${DOCKER_USERNAME:-}"
DOCKER_PASSWORD="${DOCKER_PASSWORD:-}"
DOCKER_REGISTRY_URL="${DOCKER_REGISTRY_URL:-}"

# Remove argo workflows CRDs and patch nemo's workflow controller to use namespaced mode:
kubectl get crds | grep 'argoproj.io' | awk '{print $1}' | xargs kubectl delete crd
kubectl patch deployment nemo-argo-workflows-workflow-controller --type=json -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--namespaced"}]'

# Fix too many open files error:
sudo sysctl -w fs.inotify.max_user_watches=2099999999
sudo sysctl -w fs.inotify.max_user_instances=2099999999
sudo sysctl -w fs.inotify.max_queued_events=2099999999

# Add mlrun helm:
kubectl create namespace mlrun
helm repo add mlrun-ce https://mlrun.github.io/ce
helm repo update

# Create docker registry secrets:
kubectl --namespace mlrun create secret docker-registry registry-credentials \
    --docker-server $DOCKER_SERVER \
    --docker-username $DOCKER_USERNAME \
    --docker-password=$DOCKER_PASSWORD

# Install mlrun ce:
helm --namespace mlrun install mlrun-ce --wait --timeout 960s \
  --set global.registry.url=$DOCKER_REGISTRY_URL \
  --set global.registry.secretName=registry-credentials \
  --set mlrun.api.image.tag=1.9.0-rc8 \
  --set mlrun.ui.image.tag=1.9.0-rc8 \
  --set jupyterNotebook.image.tag=1.9.0-rc8 \
  --set global.externalHostAddress=$(minikube ip) \
  --set nuclio.dashboard.externalIPAddresses=$(minikube ip) \
  mlrun-ce/mlrun-ce --version 0.7.3

# Build and push mlrun-data-flywheel image:
# log in to Docker registry:
echo $DOCKER_PASSWORD | docker login $DOCKER_SERVER -u $DOCKER_USERNAME --password-stdin

docker build -t $DOCKER_REGISTRY_URL/mlrun-data-flywheel:latest -f deploy/mlrun/Dockerfile .
docker push $DOCKER_REGISTRY_URL/mlrun-data-flywheel:latest

# Port forward all essential services and afterwards expose them in the UI:
kubectl port-forward --namespace mlrun service/mlrun-jupyter 30040:8888 --address=0.0.0.0 &
kubectl port-forward --namespace mlrun service/nuclio-dashboard 30050:8070 --address=0.0.0.0 &
kubectl port-forward --namespace mlrun service/mlrun-ui 30060:80 --address=0.0.0.0 &
kubectl port-forward --namespace mlrun service/minio-console 30090:9001 --address=0.0.0.0 &
kubectl port-forward --namespace mlrun service/grafana 30010:80 --address=0.0.0.0 &
kubectl port-forward --namespace mlrun service/monitoring-prometheus 30020:9090 --address=0.0.0.0 &