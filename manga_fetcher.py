"""
MangaDex API integration for fetching manga covers.
"""

import requests
from typing import Dict, Set, Optional


class MangaDexFetcher:
    """Fetches manga cover images from the MangaDex API."""

    BASE_URL = "https://api.mangadex.org"

    def get_manga_id(self, title: str) -> Optional[str]:
        """
        Search for a manga by title and return its ID.

        Args:
            title: Manga title to search for

        Returns:
            Manga ID string or None if not found
        """
        try:
            url = f"{self.BASE_URL}/manga"
            params = {"title": title, "limit": 1}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("result") == "ok" and data.get("data"):
                manga = data["data"][0]
                manga_id = manga.get("id")

                # Get the title to print
                attributes = manga.get("attributes", {})
                titles = attributes.get("title", {})
                # Try to get English title first, then any available title
                found_title = titles.get("en") or titles.get(
                    list(titles.keys())[0] if titles else ""
                )

                print(f"Found manga: {found_title} (ID: {manga_id})")
                return manga_id
            else:
                print(f"Warning: No manga found for title '{title}'")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to search for manga '{title}': {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"Warning: Unexpected API response format: {e}")
            return None

    def get_volume_covers(
        self, manga_id: str, volume_numbers: Set[int]
    ) -> Dict[int, str]:
        """
        Get cover URLs for specific volumes.

        Args:
            manga_id: Manga ID from MangaDex
            volume_numbers: Set of volume numbers to fetch

        Returns:
            Dictionary mapping volume numbers to cover URLs
        """
        covers = {}

        try:
            url = f"{self.BASE_URL}/cover"
            params = {"manga[]": manga_id, "limit": 100, "order[volume]": "asc"}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("result") == "ok" and data.get("data"):
                # Track which volumes we've found to avoid duplicates
                found_volumes = set()

                for cover_data in data["data"]:
                    attributes = cover_data.get("attributes", {})
                    volume_str = attributes.get("volume")

                    # Skip if no volume number
                    if not volume_str:
                        continue

                    try:
                        volume_num = int(volume_str)
                    except (ValueError, TypeError):
                        continue

                    # Only process volumes we need and haven't found yet
                    if volume_num in volume_numbers and volume_num not in found_volumes:
                        filename = attributes.get("fileName")
                        if filename:
                            # Construct the full URL
                            cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{filename}"
                            covers[volume_num] = cover_url
                            found_volumes.add(volume_num)
                            print(f"Found cover for Volume {volume_num}")

                # Warn about missing volumes
                missing = volume_numbers - found_volumes
                if missing:
                    print(
                        f"Warning: Could not find covers for volumes: {sorted(missing)}"
                    )

            return covers

        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to fetch covers: {e}")
            return covers
        except (KeyError, IndexError) as e:
            print(f"Warning: Unexpected API response format: {e}")
            return covers

    def fetch_covers(self, title: str, volumes_set: Set[int]) -> Dict[int, str]:
        """
        Orchestrate fetching covers for a manga.

        Args:
            title: Manga title
            volumes_set: Set of volume numbers to fetch

        Returns:
            Dictionary mapping volume numbers to cover URLs
        """
        if not volumes_set:
            print("No volumes to fetch")
            return {}

        manga_id = self.get_manga_id(title)
        if not manga_id:
            print(f"Warning: Could not find manga ID for '{title}'")
            return {}

        return self.get_volume_covers(manga_id, volumes_set)
