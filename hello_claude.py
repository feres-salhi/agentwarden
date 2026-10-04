from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

reply = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello to Fares in one short sentence."}],
)

print(reply.content[0].text)