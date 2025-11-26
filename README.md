# AI Recipe Planner

An intelligent meal planning application powered by AI that helps you manage ingredients, discover recipes, and plan meals based on what's in your pantry.

## Features

- 🤖 **AI-Powered Recipe Suggestions**: Get personalized recipe recommendations based on available ingredients
- 📦 **Smart Pantry Management**: Track pantry staples and fresh ingredients
- 📸 **Photo Recognition**: Upload photos of groceries to automatically update your inventory
- 💚 **Preference Learning**: The AI learns your taste preferences over time
- 📅 **Meal Planning**: Plan your weekly meals and generate shopping lists
- ✅ **Simple Interface**: Intuitive yes/no buttons and easy navigation

## Tech Stack

- **Frontend**: Next.js 14+ (React) with Tailwind CSS
- **Backend**: Next.js API routes (Node.js)
- **AI**: Anthropic Claude API (Claude 3.5 Sonnet)
- **Storage**: File-based JSON (simple and LLM-friendly)
- **Hosting**: Vercel
- **Auth**: NextAuth.js (simple password protection)

## Documentation

See [SPEC.md](./SPEC.md) for detailed product specification, architecture, and development roadmap.

## Getting Started

Coming soon - development in progress!

## Project Structure

```
/data          # JSON files for pantry, recipes, preferences
/src           # Application source code
  /app         # Next.js app directory
  /components  # React components
  /lib         # Utilities and AI agent logic
```

## License

See [LICENSE](./LICENSE) file for details.
