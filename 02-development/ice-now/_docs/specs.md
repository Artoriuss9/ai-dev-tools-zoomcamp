# IceNow MVP Specification

## Product

**IceNow** is a responsive public NHL scoreboard for coaches and players.

**Tagline:** Every game. Right now.

The MVP helps users quickly understand NHL games for yesterday, today, and tomorrow, with compact standings available alongside the game scoreboard.

## Audience and platform

- Primary audience: coaches and players
- Platform: responsive web app for desktop and mobile browsers
- Access: public, with no account required
- Optional accounts and notifications are out of scope for the MVP

## Data and time

- Start with mock data behind a replaceable internal API interface
- Integrate a licensed NHL or commercial sports-data provider later
- Use Eastern Time as the default timezone
- Display the active timezone clearly
- Support yesterday, today, and tomorrow

## Homepage

The homepage is organized around games first.

### Header

The compact header includes:

- IceNow wordmark and abstract speed/ice symbol
- Date navigation for yesterday, today, and tomorrow
- Number of live games
- Last successful refresh time

### Game layout

- Desktop: responsive grid of game cards
- Mobile: vertical list of game cards
- Sort live games first, then upcoming games chronologically, then completed games
- Use a cyan `LIVE` badge and subtle accent border for live games
- Do not rely on color alone to communicate status

### Game card

The default card shows:

- Team names and official logos when permitted by the data license
- Home and away designation
- Score
- Game status: scheduled, live, final, postponed, or canceled
- Scheduled start time

Clicking a card opens a compact summary containing:

- Venue
- Start time
- Current period or game status
- Last update time

Play-by-play, player statistics, full game center detail, and playoff analysis are out of scope.

### Standings

- Desktop: collapsible side panel
- Mobile: tab or drawer
- Fields: team, games played, wins, losses, overtime losses, points, and goal differential

### Empty and loading states

- If there are no games on a selected date, explain that clearly and link to yesterday and tomorrow
- On a first visit, use skeleton placeholders matching the game-card layout
- When cached data exists, show it immediately and refresh silently

## Refresh and failure behavior

- Automatically refresh scores every 30-60 seconds
- Show the last successful update timestamp
- When the data source is unavailable, show cached data with its timestamp
- Display an error notice and a retry action
- Never imply cached data is current without showing its age

## Accessibility

Target WCAG 2.1 AA:

- Keyboard-accessible controls and visible focus states
- Semantic headings, landmarks, buttons, and links
- Screen-reader labels for scores, statuses, date navigation, and refresh state
- Sufficient color contrast
- Status conveyed by text and structure in addition to color
- Respect reduced-motion preferences

## Visual direction

- Style: modern sports data
- Palette: white, charcoal, and electric cyan
- Typography: geometric sans-serif
- Logo: IceNow wordmark with a minimal, precise abstract speed/ice symbol
- Keep the interface clean, precise, analytical, and fast to scan

## MVP success criteria

1. Users can identify today’s live, upcoming, and completed NHL games immediately.
2. Scores and standings display a clear freshness timestamp.
3. The interface remains usable at mobile and desktop widths.
4. Keyboard and screen-reader users can navigate the full scoreboard.
5. The data layer can switch from mock data to a licensed provider without changing the UI contract.

## Out of scope

- Native mobile applications
- Required authentication
- Favorite-team personalization
- Push, email, or browser notifications
- Manual data entry
- Full-season historical browsing
- Play-by-play and player statistics
- Full game center
- Playoff analysis
