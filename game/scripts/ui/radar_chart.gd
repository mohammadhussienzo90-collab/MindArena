extends Control
## Radar/spider chart for displaying personality traits or realm stats.

@export var labels: PackedStringArray = []
@export var values: PackedFloat32Array = []
@export var max_value: float = 100.0
@export var line_color: Color = Color(0.2, 0.6, 1.0, 0.8)
@export var fill_color: Color = Color(0.2, 0.6, 1.0, 0.2)
@export var grid_color: Color = Color(1, 1, 1, 0.15)
@export var label_color: Color = Color(1, 1, 1, 0.9)


func _draw() -> void:
	if values.size() < 3:
		return

	var center = size / 2.0
	var radius = min(center.x, center.y) * 0.75
	var count = values.size()
	var angle_step = TAU / count

	# Draw grid circles
	for ring in range(1, 6):
		var r = radius * ring / 5.0
		var grid_points: PackedVector2Array = []
		for i in range(count + 1):
			var angle = -PI / 2 + angle_step * (i % count)
			grid_points.append(center + Vector2(cos(angle), sin(angle)) * r)
		draw_polyline(grid_points, grid_color, 1.0)

	# Draw axes
	for i in range(count):
		var angle = -PI / 2 + angle_step * i
		var end_point = center + Vector2(cos(angle), sin(angle)) * radius
		draw_line(center, end_point, grid_color, 1.0)

		# Draw label
		if i < labels.size():
			var label_pos = center + Vector2(cos(angle), sin(angle)) * (radius + 20)
			draw_string(
				ThemeDB.fallback_font, label_pos - Vector2(20, -5),
				labels[i], HORIZONTAL_ALIGNMENT_CENTER, -1, 12, label_color
			)

	# Draw data polygon
	var data_points: PackedVector2Array = []
	for i in range(count):
		var angle = -PI / 2 + angle_step * i
		var val_ratio = clamp(values[i] / max_value, 0.0, 1.0)
		data_points.append(center + Vector2(cos(angle), sin(angle)) * radius * val_ratio)

	if data_points.size() >= 3:
		draw_colored_polygon(data_points, fill_color)
		data_points.append(data_points[0])
		draw_polyline(data_points, line_color, 2.0)


func set_data(new_labels: PackedStringArray, new_values: PackedFloat32Array) -> void:
	labels = new_labels
	values = new_values
	queue_redraw()
