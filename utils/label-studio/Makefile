current_dir = $(shell pwd)
project_dir = $(shell pwd)/../..

setup-secrets:
	mkdir -p $(project_dir)/.secrets
	bw list --folderid "24ecd0ab-114c-4dac-9ce8-656683f328e1" --search label-studio-env items | jq -r '.[].notes' | jq -r 'keys[] as $$k | "\($$k)=\(.[$$k])"' > "$(project_dir)/.secrets/label-studio.env"

run: setup-secrets
	docker run --env-file $(project_dir)/.secrets/label-studio.env -p 8080:8080 -v "$(project_dir)/data/lable-studio:/label-studio/data" label-studio:csgo-clips-autotrim