# Runner Options

This hub repo supports three runner configurations. Choose based on your needs:

| | GitHub-hosted | Self-hosted VPS | K8s ARC |
|---|---|---|---|
| **Setup effort** | None | Low | Medium |
| **Cost** | Billed per minute | Free (your VPS) | Free (your cluster) |
| **Scaling** | Automatic | Single machine | Automatic |
| **Private network access** | No | Yes | Yes |
| **Persistent caches** | No | Yes | Partial |
| **Maintenance** | None | Runner updates | ARC + cluster |

---

## Option A — GitHub-Hosted Runners

No setup needed. GitHub provides `ubuntu-latest` runners (2 vCPU, 7 GB RAM).

In your caller workflow, set:
```yaml
runs-on: '"ubuntu-latest"'
```

**Free tier:** 2,000 minutes/month for public repos, 500 minutes/month for private repos (then $0.008/min for Linux).

---

## Option B — Self-Hosted Runner on Ubuntu VPS

Runs jobs on your own VPS. Free (you only pay for the VPS itself). Good for private network access and caching.

### One-time VPS setup

```bash
# On your Ubuntu VPS — run once per machine
sudo apt-get update && sudo apt-get install -y curl git

# Create a dedicated user (optional but recommended)
sudo useradd -m -s /bin/bash github-runner
sudo su - github-runner
```

### Register the runner

1. Go to **GitHub → your repo (or org) → Settings → Actions → Runners → New self-hosted runner**
2. Select **Linux / x64**
3. Follow the displayed commands — they look like:

```bash
# Download
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/vX.Y.Z/actions-runner-linux-x64-X.Y.Z.tar.gz
tar xzf ./actions-runner-linux-x64.tar.gz

# Configure (paste the token shown in GitHub's UI)
./config.sh --url https://github.com/YOUR_ORG_OR_USER --token YOUR_TOKEN \
  --labels "self-hosted,linux" --name "vps-runner-1"

# Install as a systemd service so it survives reboots
sudo ./svc.sh install github-runner
sudo ./svc.sh start
```

4. Verify the runner appears as **Idle** in GitHub's UI.

### Caller workflow config

```yaml
runs-on: '["self-hosted","linux"]'
```

### Maintenance

```bash
# Update the runner (check GitHub for latest version)
sudo ./svc.sh stop
./config.sh remove --token YOUR_TOKEN
# Re-download and re-configure with the new version
```

---

## Option C — Self-Hosted Runners on Kubernetes (ARC)

[Actions Runner Controller (ARC)](https://github.com/actions/actions-runner-controller) runs ephemeral runner pods on your cluster. Each job gets a fresh pod; pods are torn down after the job completes.

### Prerequisites

- `kubectl` configured pointing at your cluster
- `helm` v3 installed locally
- Kubernetes cluster running on your VPS (e.g., k3s, k0s, or kubeadm)

### Install k3s on your VPS (if you don't have a cluster)

```bash
# On your VPS
curl -sfL https://get.k3s.io | sh -
# Copy kubeconfig locally
sudo cat /etc/rancher/k3s/k3s.yaml  # then copy to ~/.kube/config
```

### Install ARC

```bash
# Add the Helm chart repo
helm repo add actions-runner-controller \
  https://actions-runner-controller.github.io/actions-runner-controller
helm repo update

# Install the controller into its own namespace
helm install arc \
  --namespace arc-systems \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
```

### Create a GitHub PAT

Go to **GitHub → Settings → Developer settings → Personal access tokens (fine-grained)**

Required permissions:
- **Repository**: Actions (read/write), Administration (read/write) — for repo-scoped runners
- **Organization**: Self-hosted runners (read/write) — for org-scoped runners

### Deploy a runner scale set

```bash
# Create namespace for runners
kubectl create namespace arc-runners

# Store the PAT as a secret
kubectl create secret generic gh-pat \
  --namespace arc-runners \
  --from-literal=github_token=YOUR_PAT

# Install a runner scale set (replace values as needed)
helm install my-python-runners \
  --namespace arc-runners \
  --set githubConfigUrl="https://github.com/YOUR_ORG_OR_USER" \
  --set githubConfigSecret=gh-pat \
  --set runnerScaleSetName="k8s" \
  --set minRunners=0 \
  --set maxRunners=5 \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```

The `runnerScaleSetName` value (here `"k8s"`) becomes the runner label.

### Verify

```bash
kubectl get pods -n arc-runners
kubectl get pods -n arc-systems
```

You should see the controller pod running. Runner pods appear on-demand when jobs are queued.

### Caller workflow config

```yaml
# Use the runnerScaleSetName you set above
runs-on: '["self-hosted","linux","k8s"]'
```

### Customizing the runner image

By default, ARC uses the official `ghcr.io/actions/actions-runner` image. To add Python or other tools:

```dockerfile
# Dockerfile.runner
FROM ghcr.io/actions/actions-runner:latest
USER root
RUN apt-get update && apt-get install -y python3 python3-pip git
USER runner
```

Then in your `helm install` command, add:
```bash
--set template.spec.containers[0].image=YOUR_REGISTRY/custom-runner:latest
```

---

## Switching between runner types

In [example-caller.yml](../.github/workflows/example-caller.yml), change the `runs-on` input:

```yaml
# GitHub-hosted
runs-on: '"ubuntu-latest"'

# Self-hosted VPS
runs-on: '["self-hosted","linux"]'

# K8s ARC (replace "k8s" with your runnerScaleSetName)
runs-on: '["self-hosted","linux","k8s"]'
```
