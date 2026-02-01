# Trigger Creation Mode - Quick Start Guide

## How to Use Trigger Creation Mode

### Starting Creation Mode

1. **Run the application** with any configuration file:
   ```bash
   python video-midi-trigger.py camera
   # or
   python video-midi-trigger.py your-config
   ```

2. **Press 'c'** to enter creation mode. You'll see:
   ```
   === CREATION MODE ===
   Click on the window to add points to the new trigger.
   Press BACKSPACE to remove the last point.
   Press ENTER to save and exit creation mode.
   =====================
   ```

### Creating a Trigger

#### Example: Creating a Triangle Trigger

1. **First Click** - Top point
   - Click anywhere on the video (e.g., center-top)
   - Console shows: `Creating new trigger based on 'Previous Trigger Name'`
   - Console shows: `Added point 1: [50.0, 20.0]`

2. **Second Click** - Bottom-left point
   - Click bottom-left area
   - Console shows: `Added point 2: [30.0, 70.0]`

3. **Third Click** - Bottom-right point
   - Click bottom-right area
   - Console shows: `Added point 3: [70.0, 70.0]`

4. **Press ENTER** to save
   - Console shows: `Saved new trigger with 3 points.`
   - Console shows: `Configuration saved to your-config.yaml`
   - Trigger is immediately active and visible

### Correcting Mistakes

**Remove the Last Point:**
- Press **BACKSPACE**
- Console shows: `Removed point: [70.0, 70.0]. 2 points remaining.`

**Cancel Creation:**
- Keep pressing BACKSPACE until all points are removed
- Press ENTER
- Console shows: `No points added. Discarding trigger and exiting creation mode.`

### Supported Shapes

#### Single Pixel (1 point)
- Click once
- Press ENTER
- Creates a single-pixel trigger

#### Line (2 points)
- Click start point
- Click end point
- Press ENTER

#### Triangle (3 points)
- Click three corners
- Press ENTER

#### Polygon (4+ points)
- Click as many corners as needed
- The shape will be filled
- Press ENTER when done

### Tips

1. **Click Precision**: Coordinates are rounded to 1 decimal place for cleaner YAML files

2. **Based on Last Trigger**: The new trigger inherits all settings (type, threshold, MIDI config) from the last trigger in your config file

3. **Comments Preserved**: Your YAML comments and formatting are preserved when the file is saved

4. **Immediate Feedback**: You can see each point's coordinates in the console as you click

5. **No Minimum Points**: You can create triggers with any number of points (even 1)

### Example Workflow

```
1. Press 'c'                    → Enter creation mode
2. Click (50, 20)              → Add point 1 (top)
3. Click (25, 60)              → Add point 2 (bottom-left)
4. Click (75, 60)              → Add point 3 (bottom-right)
5. Press BACKSPACE             → Remove point 3 (oops!)
6. Click (70, 65)              → Add corrected point 3
7. Press ENTER                 → Save and exit
```

Result: New triangle trigger created with 3 points!

### What Gets Duplicated

From the last trigger:
- ✅ Name (you may want to edit the YAML file to rename it)
- ✅ Type (brightness, motion, difference, etc.)
- ✅ Threshold or range settings
- ✅ MIDI note/CC and velocity
- ✅ MIDI channel
- ✅ Debounce and throttle settings
- ✅ Color settings
- ✅ Device settings

What changes:
- ❌ Position (removed)
- ✅ Shape (replaced with your new points)

### After Creation

The new trigger is added to the end of your YAML file and is immediately active. You can:

1. **Edit the YAML file** to:
   - Rename the trigger
   - Adjust threshold, MIDI settings, etc.
   - Fine-tune coordinates if needed

2. **The app auto-reloads** when you save YAML changes (except for source and global device settings)

3. **Create more triggers** by pressing 'c' again

### Keyboard Reference

| Key | Action |
|-----|--------|
| `c` | Enter creation mode |
| Click | Add point to shape |
| `BACKSPACE` | Remove last point |
| `ENTER` | Save trigger and exit creation mode |
| `q` | Quit application |
| `r` | Restart video |
| `h` | Hide/show triggers |

## Troubleshooting

**Q: Nothing happens when I click**
- Make sure you pressed 'c' first to enter creation mode
- Check the console for the "=== CREATION MODE ===" message

**Q: I can't create a trigger**
- Make sure you have at least one trigger in your YAML file already
- The first click duplicates the last trigger

**Q: My YAML comments disappeared**
- This shouldn't happen with ruamel.yaml, but if it does:
- Make a backup of your YAML file first
- Report the issue

**Q: The trigger isn't working**
- Check that the trigger's type and threshold make sense for your use case
- Remember it's based on the last trigger, which might have different settings
- Edit the YAML file to adjust settings

**Q: I want to delete a trigger**
- Currently, you need to manually edit the YAML file
- Future versions may add this feature

## Example Configurations

See the test files for examples:
- `shapes-test.yaml` - Various shape types
- `test-creation.yaml` - Simple test configuration
