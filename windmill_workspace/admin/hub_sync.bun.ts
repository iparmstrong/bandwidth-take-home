import * as wmill from "windmill-cli@1.566.1"

export async function main() {
  await wmill.hubPull({ workspace: "admins", token: process.env["WM_TOKEN"], baseUrl: process.env["BASE_URL"] });
}
