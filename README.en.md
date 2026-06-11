# DesignFordrink / Troitsa

Multi-model decision workflow: Conductor + Worker + Critic.

DeepSeek V4 Pro plans, DeepSeek V4 Flash does the volume, Owl Alpha tries to break the result. Better quality + lower cost than one model.

## Models

| Role | Model | Provider |
|------|-------|----------|
| Conductor | DeepSeek V4 Pro | OpenRouter |
| Worker | DeepSeek V4 Flash | OpenRouter |
| Critic | Owl Alpha | OpenRouter |

## Usage

```bash
hermes skills install "https://raw.githubusercontent.com/designfordrink/troitsa/main/SKILL.md"
```

In Hermes session: `/skill troitsa`

Triggers: `troitsa`, `council`, `red team this`, `plan-execute-critique`

## License

MIT