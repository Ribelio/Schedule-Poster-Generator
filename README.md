# Schedule Poster Generator

A Python tool for generating beautiful visual schedule posters for manga book clubs. This project creates stylized posters featuring manga volume covers arranged in a sleek, modern layout with dates and volume information.

## Features

- 🎨 **Visual Schedule Posters**: Generate eye-catching posters with manga volume covers
- 📅 **Customizable Schedule**: Easy-to-edit schedule configuration
- 🖼️ **Automatic Image Loading**: Fetches volume covers from URLs automatically
- 🎯 **Smart Image Processing**: Center-crop and zoom functionality to focus on character art
- 📐 **Dynamic Layout**: Automatically adjusts layout based on number of schedule items
- 🎭 **Stylized Design**: Parallelogram frames with drop shadows and modern dark theme

## Screenshot

The generated poster displays your manga club schedule with volume covers in an elegant grid layout.

## Requirements

- Python 3.8 or higher
- Dependencies (see Installation section)

## Installation

### Option 1: Using Pixi (Recommended)

This project uses [Pixi](https://pixi.sh/) for dependency management. If you don't have Pixi installed, you can install it from [pixi.sh](https://pixi.sh/).

```bash
# Install dependencies
pixi install

# Activate the environment
pixi shell
```

### Option 2: Using pip

If you prefer using pip, install the dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Usage

1. **Configure the schedule**: Edit the `schedule` list in `schedule.py` with your dates and volume numbers:
   ```python
   schedule = [
       ("November 22, 2025", [2, 3]),
       ("November 29, 2025", [4, 5]),
       # Add more dates and volumes...
   ]
   ```

2. **Add volume cover URLs**: Update the `cover_urls` dictionary with URLs for each volume:
   ```python
   cover_urls = {
       1: "https://example.com/volume1.jpg",
       2: "https://example.com/volume2.jpg",
       # Add more volumes...
   }
   ```

3. **Run the script**:
   ```bash
   # If using Pixi
   pixi run python schedule.py
   
   # Or if using pip
   python schedule.py
   ```

4. **Output**: The script will generate `choujin_x_schedule_fixed.png` in the project directory.

## Configuration Options

You can customize the poster appearance by modifying these variables in `schedule.py`:

- **`ZOOM_FACTOR`** (default: `0.95`): Controls how much the images are zoomed/cropped. Higher values = more zoom into center.
- **`VERTICAL_OFFSET`** (default: `-0.1`): Adjusts vertical positioning of images. Positive values move images higher.
- **`title_row_height`**: Height reserved for the title (default: `3.0`)
- **`fig_width`**: Overall poster width (default: `16`)
- **`frame_width`** and **`frame_height`**: Dimensions of the parallelogram frames
- **`skew_angle`**: Angle of the parallelogram skew in degrees (default: `15`)

## Project Structure

```
Schedule-Poster-Generator/
├── schedule.py              # Main script
├── pixi.toml                # Pixi dependency configuration
├── pixi.lock                # Pixi lock file
├── requirements.txt         # pip requirements (alternative to pixi)
├── README.md                # This file
├── .gitignore              # Git ignore rules
└── .gitattributes          # Git attributes
```

## Customization

### Changing the Title

Edit the title text in `schedule.py`:
```python
ax.text(fig_width / 2, title_y, "Your Custom Title Here",
        ha='center', va='center', fontsize=42, fontweight='bold',
        color='white', fontfamily='Courier New',
        path_effects=[withStroke(linewidth=3, foreground='#1a1a1a')])
```

### Changing Colors

The poster uses a dark theme (`#1a1a1a` background). You can modify:
- Background color: `fig.patch.set_facecolor('#1a1a1a')`
- Text color: `color='white'` in text elements
- Frame border color: `edgecolor='white'` in the Polygon

### Adjusting Layout

- **Grid columns**: Change `cols = 2` to adjust the number of columns
- **Spacing**: Modify `vertical_padding` and `frame_spacing` variables
- **Figure size**: Adjust `fig_width` and `fig_height` calculations

## Troubleshooting

### Images Not Loading

If volume covers fail to load:
- Check that the URLs in `cover_urls` are valid and accessible
- Some websites may block automated requests; you may need to update the User-Agent header
- The script will display "Image N/A" for failed loads

### Output Image Issues

- If the layout looks off, adjust `fig_width`, `fig_height`, or spacing parameters
- If images are cropped incorrectly, adjust `ZOOM_FACTOR` or `VERTICAL_OFFSET`
- Increase `dpi` in `plt.savefig()` for higher resolution output

## Contributing

Feel free to submit issues or pull requests to improve this tool for the manga club!

## License

This project is for use by the manga club community.

## Credits

Created for the manga club to generate beautiful schedule posters for reading sessions.
