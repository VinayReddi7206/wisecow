# Wisecow on Kubernetes — Containerisation, CI/CD & TLS

Containerise and deploy the [Wisecow](https://github.com/nyrahul/wisecow) application
on Kubernetes with an automated CI/CD pipeline and secure TLS communication.
Completed as the **AccuKnox DevOps Trainee Practical Assessment**.

Wisecow serves a random fortune wrapped in an ASCII cow (`fortune | cowsay`) over
HTTP on port **4499** using `netcat`.

---

## Repository layout

```
.
├── wisecow.sh                     # the application
├── Dockerfile                     # container image definition
├── k8s/
│   ├── deployment.yaml            # Deployment (2 replicas)
│   ├── service.yaml               # ClusterIP service (80 -> 4499)
│   ├── ingress.yaml               # HTTPS ingress (TLS)
│   └── gen-certs.sh               # generates self-signed cert + TLS secret
├── .github/workflows/
│   └── ci-cd.yaml                 # build+push (CI) and deploy (CD)
├── scripts/
│   ├── system_health.py           # PS2 #1 — system health monitor
│   └── app_health_checker.py      # PS2 #4 — app up/down checker
├── kubearmor/
│   └── policy.yaml                # PS3 — zero-trust KubeArmor policy
└── screenshots/
    └── violation.png              # PS3 — KubeArmor violation screenshot
```

---

## Problem Statement 1 — Containerisation & Deployment

### 1. Build & run the container locally
```bash
docker build -t wisecow:local .
docker run -p 4499:4499 wisecow:local
# open http://localhost:4499 in your browser -> you should see the cow
```

### 2. Deploy to Kubernetes (Minikube)
```bash
minikube start
minikube addons enable ingress          # NGINX ingress controller (for TLS)

# generate the self-signed TLS certificate + secret
cd k8s && chmod +x gen-certs.sh && ./gen-certs.sh && cd ..

kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

kubectl get pods,svc,ingress            # verify everything is running
```

### 3. Access over secure TLS (HTTPS)
Add this line to your hosts file
(`C:\Windows\System32\drivers\etc\hosts` on Windows, `/etc/hosts` on Linux/Mac):
```
127.0.0.1  wisecow.local
```
Then (Minikube):
```bash
minikube tunnel        # keep this running in a separate terminal
```
Open **https://wisecow.local** — the app is served over HTTPS. The browser will
warn about the self-signed certificate; that is expected (proceed anyway).

---

## Continuous Integration & Deployment (CI/CD)

The pipeline lives in [`.github/workflows/ci-cd.yaml`](.github/workflows/ci-cd.yaml).

**CI — `build-and-push` (GitHub-hosted runner)**
On every push to `main` it builds the Docker image and pushes it to
**GitHub Container Registry** (`ghcr.io/<user>/wisecow`) using the built-in
`GITHUB_TOKEN` — no extra secrets needed.

**CD — `deploy` (self-hosted runner)**
After a successful build it runs `kubectl apply` + `kubectl rollout` to deploy the
new image. Because a local Minikube/Kind cluster is **not reachable from GitHub's
cloud runners**, the deploy job runs on a **self-hosted runner** on the machine
where the cluster lives.

### One-time: register the self-hosted runner
On the machine running your cluster:
`GitHub repo → Settings → Actions → Runners → New self-hosted runner`, then follow
the shown commands (download, `./config.sh …`, `./run.sh`). The runner picks up the
`deploy` job automatically. Make sure `kubectl` on that machine targets your cluster.

> Prefer the cloud? Point the deploy job at a managed cluster (EKS/AKS/GKE) via a
> `KUBECONFIG` secret and change `runs-on:` back to `ubuntu-latest`.

---

## Problem Statement 2 — Scripts (Bash/Python)

Two objectives implemented in Python (chosen: **#1** and **#4**).

### #1 System Health Monitor — `scripts/system_health.py`
Checks CPU, memory, disk and process count; alerts to console **and**
`system_health.log` when a threshold is exceeded.
```bash
pip install psutil
python3 scripts/system_health.py              # one check
python3 scripts/system_health.py --watch 5    # every 5s
python3 scripts/system_health.py --cpu 50     # custom threshold (demo an alert)
```

### #4 Application Health Checker — `scripts/app_health_checker.py`
Reports **UP/DOWN** from the HTTP status code (standard library only).
```bash
python3 scripts/app_health_checker.py https://wisecow.local --insecure
python3 scripts/app_health_checker.py http://localhost:4499 --watch 10
```
(`--insecure` skips TLS verification for our self-signed certificate.)

---

## Problem Statement 3 — Zero-Trust KubeArmor policy (bonus)

[`kubearmor/policy.yaml`](kubearmor/policy.yaml) locks the Wisecow pod down to
least privilege: it **blocks** reading credential files (`/etc/shadow`, the
service-account token) and executing tooling the app never needs (`apt`, `curl`,
`wget`, …).

### Install KubeArmor & apply the policy
```bash
# install KubeArmor (karmor CLI)
curl -sfL https://raw.githubusercontent.com/kubearmor/KubeArmor/main/getting-started/kubearmor_client.sh | sudo bash
karmor install

kubectl apply -f kubearmor/policy.yaml
```

### Trigger a violation and capture the screenshot
```bash
# stream policy-violation alerts (keep running)
karmor logs --json

# in another terminal, do something the policy forbids:
POD=$(kubectl get pod -l app=wisecow -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD -- cat /etc/shadow      # -> Permission denied (BLOCKED)
```
`karmor logs` prints a violation event. Screenshot it and save to
`screenshots/violation.png`.

---

## Assessment checklist
- [x] Dockerfile
- [x] Kubernetes manifests (Deployment + Service)
- [x] App exposed as a Service
- [x] GitHub Actions CI (build + push image)
- [x] Continuous Deployment to Kubernetes (self-hosted runner)
- [x] TLS / HTTPS communication
- [x] PS2: two scripts (system health + app health)
- [x] PS3: zero-trust KubeArmor policy + violation screenshot
- [x] Public GitHub repository
