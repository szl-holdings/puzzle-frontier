import { Container } from "@cloudflare/containers";

export class PuzzleApiContainer extends Container {
  defaultPort = 8080;
}

export default {
  async fetch(request, env) {
    const id = env.PUZZLE_API.idFromName("primary");
    const stub = env.PUZZLE_API.get(id);
    return stub.fetch(request);
  },
};