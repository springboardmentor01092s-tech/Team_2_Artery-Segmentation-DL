"""Small reproducible U-Net baseline for binary ARCADE masks."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps


MODEL_SIZE = 128


def prepare_input(path: Path | Image.Image, size: int = MODEL_SIZE) -> np.ndarray:
    if isinstance(path, Image.Image):
        image = path.convert("L").resize((size, size), Image.Resampling.BILINEAR)
    else:
        with Image.open(path) as opened:
            image = opened.convert("L").resize((size, size), Image.Resampling.BILINEAR)
    image = ImageOps.autocontrast(image.filter(ImageFilter.MedianFilter(3)), cutoff=1)
    return np.asarray(image, dtype=np.float32)[None] / 255.0


def prepare_mask(path: Path | Image.Image, size: int = MODEL_SIZE) -> np.ndarray:
    if isinstance(path, Image.Image):
        image = path.convert("L").resize((size, size), Image.Resampling.NEAREST)
    else:
        with Image.open(path) as opened:
            image = opened.convert("L").resize((size, size), Image.Resampling.NEAREST)
    return (np.asarray(image) > 0).astype(np.float32)[None]


def overlay_png(source: Path, artery: np.ndarray, stenosis: np.ndarray) -> bytes:
    with Image.open(source) as opened:
        base = opened.convert("RGB")
    size = base.size
    artery_mask = Image.fromarray((artery > 0.5).astype(np.uint8) * 255).resize(size, Image.Resampling.NEAREST)
    stenosis_mask = Image.fromarray((stenosis > 0.5).astype(np.uint8) * 255).resize(size, Image.Resampling.NEAREST)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    layer.paste((0, 180, 210, 105), mask=artery_mask)
    artery_gray = artery_mask.convert("L")
    artery_boundary = ImageChops.subtract(artery_gray, artery_gray.filter(ImageFilter.MinFilter(3)))
    layer.paste((56, 238, 255, 235), mask=artery_boundary)
    layer.paste((240, 89, 73, 180), mask=stenosis_mask)
    result = Image.alpha_composite(base.convert("RGBA"), layer)
    buffer = BytesIO()
    result.save(buffer, format="PNG")
    return buffer.getvalue()


def heatmap_overlay_png(source: Path, heatmap: np.ndarray, palette: str = "hot") -> bytes:
    """Render an explicitly uncalibrated model map over the source image."""
    with Image.open(source) as opened:
        base = opened.convert("RGB")
    values = np.clip(np.asarray(heatmap, dtype=np.float32), 0, 1)
    gray = Image.fromarray(np.uint8(values * 255)).resize(base.size, Image.Resampling.BILINEAR)
    values = np.asarray(gray, dtype=np.float32) / 255
    if palette == "attention":
        color = np.stack((values * 255, (1 - np.abs(values - 0.5) * 2) * 190, (1 - values) * 255), axis=-1)
    else:
        color = np.stack((np.minimum(1, values * 2) * 255,
                          np.maximum(0, values * 2 - 0.65) * 255,
                          np.maximum(0, values * 3 - 2) * 255), axis=-1)
    heat = Image.fromarray(np.uint8(np.clip(color, 0, 255)), "RGB")
    result = Image.blend(base, heat, 0.48)
    buffer = BytesIO()
    result.save(buffer, format="PNG")
    return buffer.getvalue()


def centerline_overlay_png(source: Path, paths: list[dict], branch_points: list[dict],
                           endpoint_points: list[dict], artery_mask: np.ndarray | None = None,
                           model_size: int = MODEL_SIZE) -> bytes:
    """Draw algorithmic centerline paths and graph-node labels over a source frame."""
    from PIL import ImageDraw

    with Image.open(source) as opened:
        canvas = opened.convert("RGB")
    if artery_mask is not None:
        alpha = Image.fromarray(np.uint8(np.asarray(artery_mask, dtype=bool) * 255)).resize(
            canvas.size, Image.Resampling.NEAREST)
        vessel_layer = Image.new("RGBA", canvas.size, (0, 180, 210, 60))
        vessel_layer.putalpha(alpha.point(lambda value: round(value * 0.28)))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), vessel_layer).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    scale_x = max(canvas.width - 1, 1) / max(model_size - 1, 1)
    scale_y = max(canvas.height - 1, 1) / max(model_size - 1, 1)

    def to_source(point):
        return (round(float(point[0]) * scale_x), round(float(point[1]) * scale_y))

    for path in paths:
        coordinates = [to_source(point) for point in path.get("coordinates_xy", [])]
        if len(coordinates) >= 2:
            draw.line(coordinates, fill=(34, 238, 243), width=max(2, round(min(canvas.size) / 280)))
    radius = max(4, round(min(canvas.size) / 90))
    for point in endpoint_points:
        x, y = to_source((point["x"], point["y"]))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(40, 226, 115), outline=(5, 40, 20), width=2)
    for point in branch_points:
        x, y = to_source((point["x"], point["y"]))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 210, 56), outline=(64, 43, 0), width=2)
        draw.text((x + radius + 2, y - radius - 2), point["node_id"], fill=(255, 244, 187), stroke_width=2, stroke_fill=(20, 20, 20))
    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()


def postprocess_mask(mask: np.ndarray, minimum_component_pixels: int = 3) -> np.ndarray:
    """Remove tiny 8-connected islands and fill single-pixel holes without SciPy."""
    binary = np.asarray(mask, dtype=bool).copy()
    if binary.ndim != 2:
        raise ValueError("mask must be two-dimensional")
    height, width = binary.shape
    visited = np.zeros_like(binary)
    for y in range(height):
        for x in range(width):
            if not binary[y, x] or visited[y, x]:
                continue
            stack, component = [(y, x)], []
            visited[y, x] = True
            while stack:
                cy, cx = stack.pop()
                component.append((cy, cx))
                for ny in range(max(0, cy - 1), min(height, cy + 2)):
                    for nx in range(max(0, cx - 1), min(width, cx + 2)):
                        if binary[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            stack.append((ny, nx))
            if len(component) < minimum_component_pixels:
                for cy, cx in component:
                    binary[cy, cx] = False
    if height > 2 and width > 2:
        center = binary[1:-1, 1:-1]
        neighbors = sum(binary[1 + dy:height - 1 + dy, 1 + dx:width - 1 + dx]
                        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        center[(~center) & (neighbors == 4)] = True
    return binary


def _skeletonize(mask: np.ndarray) -> np.ndarray:
    """Zhang-Suen thinning for a binary 2D mask; returns a one-pixel skeleton."""
    image = np.asarray(mask, dtype=np.uint8).copy()
    if image.ndim != 2:
        raise ValueError("mask must be two-dimensional")
    image[[0, -1], :] = 0
    image[:, [0, -1]] = 0
    changed = True
    while changed:
        changed = False
        for phase in (0, 1):
            p2 = image[:-2, 1:-1]
            p3 = image[:-2, 2:]
            p4 = image[1:-1, 2:]
            p5 = image[2:, 2:]
            p6 = image[2:, 1:-1]
            p7 = image[2:, :-2]
            p8 = image[1:-1, :-2]
            p9 = image[:-2, :-2]
            center = image[1:-1, 1:-1]
            ring = (p2, p3, p4, p5, p6, p7, p8, p9)
            count = sum(ring)
            transitions = sum(((ring[index] == 0) & (ring[(index + 1) % 8] == 1)) for index in range(8))
            if phase == 0:
                condition_a = (p2 * p4 * p6) == 0
                condition_b = (p4 * p6 * p8) == 0
            else:
                condition_a = (p2 * p4 * p8) == 0
                condition_b = (p2 * p6 * p8) == 0
            remove = (center == 1) & (count >= 2) & (count <= 6) & (transitions == 1) & condition_a & condition_b
            if np.any(remove):
                center[remove] = 0
                changed = True
    return image.astype(bool)


def analyze_vessel_geometry(mask: np.ndarray, spacing_mm: tuple[float, float] | None = None,
                            probability_map: np.ndarray | None = None,
                            threshold: float = 0.5) -> dict:
    """Describe 2D mask topology, approximate centerlines, and local mask widths."""
    binary = postprocess_mask(mask)
    probabilities = None if probability_map is None else np.asarray(probability_map, dtype=np.float32)
    if probabilities is not None and (probabilities.shape != binary.shape or not np.isfinite(probabilities).all()):
        raise ValueError("probability_map must be finite and match the binary mask shape")
    if probabilities is not None and (np.any(probabilities < 0) or np.any(probabilities > 1)):
        raise ValueError("probability_map values must be within [0, 1]")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    skeleton = _skeletonize(binary)
    height, width = binary.shape
    calibrated = bool(spacing_mm and len(spacing_mm) == 2 and all(value > 0 for value in spacing_mm))
    unit = "mm" if calibrated else "px"
    sy, sx = spacing_mm if calibrated else (1.0, 1.0)

    def neighbors(point, points):
        y, x = point
        found = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                candidate = (y + dy, x + dx)
                if not (dy or dx) or candidate not in points:
                    continue
                if dy and dx and ((y + dy, x) in points or (y, x + dx) in points):
                    continue
                found.append(candidate)
        return found

    def edge_length(left, right):
        return float(np.hypot((right[0] - left[0]) * sy, (right[1] - left[1]) * sx))

    # Connected artery-mask components become independent vessel candidates.
    labels = np.zeros(binary.shape, dtype=np.int32)
    components = []
    for y, x in np.argwhere(binary):
        if labels[y, x]:
            continue
        component_id = len(components) + 1
        stack, pixels = [(int(y), int(x))], []
        labels[y, x] = component_id
        while stack:
            cy, cx = stack.pop()
            pixels.append((cy, cx))
            for ny in range(max(0, cy - 1), min(height, cy + 2)):
                for nx in range(max(0, cx - 1), min(width, cx + 2)):
                    if binary[ny, nx] and not labels[ny, nx]:
                        labels[ny, nx] = component_id
                        stack.append((ny, nx))
        components.append(pixels)

    skeleton_points = {tuple(map(int, point)) for point in np.argwhere(skeleton)}
    adjacency = {point: neighbors(point, skeleton_points) for point in skeleton_points}
    degree = {point: len(items) for point, items in adjacency.items()}
    endpoints = [point for point, value in degree.items() if value == 1]
    junction_pixels = {point for point, value in degree.items() if value >= 3}

    # Adjacent junction pixels form one branching location in the thinned graph.
    junction_groups, junction_seen = [], set()
    for point in sorted(junction_pixels):
        if point in junction_seen:
            continue
        stack = [point]
        group = []
        junction_seen.add(point)
        while stack:
            current = stack.pop()
            group.append(current)
            for neighbor in adjacency[current]:
                if neighbor in junction_pixels and neighbor not in junction_seen:
                    junction_seen.add(neighbor)
                    stack.append(neighbor)
        junction_groups.append(sorted(group))
    junction_count = len(junction_groups)
    junction_node_for_pixel = {point: f"J{index + 1}" for index, group in enumerate(junction_groups) for point in group}
    endpoint_node_for_pixel = {point: f"E{index + 1}" for index, point in enumerate(sorted(endpoints))}
    graph_node_ids = {**endpoint_node_for_pixel, **junction_node_for_pixel}
    branch_points = []
    for index, group in enumerate(junction_groups):
        cy, cx = np.mean(group, axis=0)
        representative = min(group, key=lambda point: (point[0] - cy) ** 2 + (point[1] - cx) ** 2)
        branch_points.append({"node_id": f"J{index + 1}", "x": representative[1], "y": representative[0]})
    endpoint_points = [{"node_id": endpoint_node_for_pixel[point], "x": point[1], "y": point[0]}
                       for point in sorted(endpoints)]

    # Label skeleton components and calculate their centerline lengths.
    skeleton_components, seen = [], set()
    for point in skeleton_points:
        if point in seen:
            continue
        stack, group = [point], []
        seen.add(point)
        while stack:
            current = stack.pop()
            group.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        skeleton_components.append(group)

    def path_distances(start, allowed):
        import heapq
        distances, pending = {start: 0.0}, [(0.0, start)]
        while pending:
            distance, current = heapq.heappop(pending)
            if distance != distances[current]:
                continue
            for neighbor in adjacency[current]:
                if neighbor not in allowed:
                    continue
                proposed = distance + edge_length(current, neighbor)
                if proposed < distances.get(neighbor, float("inf")):
                    distances[neighbor] = proposed
                    heapq.heappush(pending, (proposed, neighbor))
        return distances

    def edge_key(left, right):
        return (left, right) if left < right else (right, left)

    # Trace maximal skeleton paths between endpoint/junction nodes. Junction
    # clusters are contracted conceptually: internal cluster edges are omitted.
    critical_points = set(endpoints) | set(junction_pixels)
    visited_edges, centerline_paths = set(), []
    for start in sorted(critical_points):
        for first in adjacency[start]:
            if (start in junction_node_for_pixel and first in junction_node_for_pixel
                    and junction_node_for_pixel[start] == junction_node_for_pixel[first]):
                continue
            if edge_key(start, first) in visited_edges:
                continue
            coordinates = [start]
            previous, current = start, first
            while True:
                visited_edges.add(edge_key(previous, current))
                coordinates.append(current)
                if current in critical_points:
                    break
                next_points = [point for point in adjacency[current]
                               if point != previous and edge_key(current, point) not in visited_edges]
                if not next_points:
                    break
                previous, current = current, min(next_points)
                if len(coordinates) > len(skeleton_points) + 1:
                    break
            if len(coordinates) > 1:
                path_length = sum(edge_length(left, right) for left, right in zip(coordinates, coordinates[1:]))
                centerline_paths.append({
                    "path_id": f"P{len(centerline_paths) + 1}", "path_type": "centerline",
                    "start_node": graph_node_ids.get(coordinates[0]),
                    "end_node": graph_node_ids.get(coordinates[-1]),
                    "length": round(path_length, 2), "length_unit": unit,
                    "coordinates_xy": [[point[1], point[0]] for point in coordinates],
                })

    # Components with only degree-two pixels are loops; degree-zero components
    # are isolated skeleton pixels. Preserve both instead of dropping them.
    for group in skeleton_components:
        group_set = set(group)
        if any(point in critical_points for point in group):
            continue
        if len(group) == 1 and degree[group[0]] == 0:
            point = group[0]
            centerline_paths.append({"path_id": f"P{len(centerline_paths) + 1}", "path_type": "isolated",
                                     "start_node": None, "end_node": None, "length": 0.0,
                                     "length_unit": unit, "coordinates_xy": [[point[1], point[0]]]})
            continue
        start = min(group)
        first_points = sorted(adjacency[start])
        if not first_points:
            continue
        coordinates, previous, current = [start], start, first_points[0]
        while True:
            if edge_key(previous, current) in visited_edges:
                break
            visited_edges.add(edge_key(previous, current))
            coordinates.append(current)
            if current == start:
                break
            next_points = [point for point in adjacency[current]
                           if point != previous and point in group_set and edge_key(current, point) not in visited_edges]
            if not next_points:
                break
            previous, current = current, min(next_points)
            if len(coordinates) > len(group) + 1:
                break
        if len(coordinates) > 2:
            path_length = sum(edge_length(left, right) for left, right in zip(coordinates, coordinates[1:]))
            centerline_paths.append({"path_id": f"P{len(centerline_paths) + 1}", "path_type": "cycle",
                                     "start_node": None, "end_node": None, "length": round(path_length, 2),
                                     "length_unit": unit,
                                     "coordinates_xy": [[point[1], point[0]] for point in coordinates]})

    centerline_length, max_tortuosity = 0.0, None
    component_skeleton_counts = {}
    for group in skeleton_components:
        group_set = set(group)
        group_length = sum(edge_length(point, neighbor) for point in group
                           for neighbor in adjacency[point] if neighbor in group_set and point < neighbor)
        centerline_length += group_length
        component_id = int(labels[group[0]]) if group else 0
        component_skeleton_counts[component_id] = max(component_skeleton_counts.get(component_id, 0), len(group))
        tips = [point for point in group if degree[point] == 1]
        if len(tips) >= 2:
            first_distances = path_distances(tips[0], group_set)
            far_tip = max(tips, key=lambda tip: first_distances.get(tip, 0.0))
            distances = path_distances(far_tip, group_set)
            other_tip = max(tips, key=lambda tip: distances.get(tip, 0.0))
            geodesic = distances.get(other_tip, 0.0)
            euclidean = edge_length(far_tip, other_tip)
            if euclidean > 0:
                ratio = geodesic / euclidean
                max_tortuosity = ratio if max_tortuosity is None else max(max_tortuosity, ratio)

    # Estimate local diameter from each sampled skeleton point to mask boundary.
    background = np.argwhere(~binary)
    sample_points = sorted(skeleton_points)[::max(1, len(skeleton_points) // 1500)] if skeleton_points else []
    diameters = []
    if len(background):
        for y, x in sample_points:
            distances = np.hypot((background[:, 0] - y) * sy, (background[:, 1] - x) * sx)
            radius = float(distances.min())
            if radius > 0:
                diameters.append(2 * radius)

    # Count exposed horizontal and vertical mask edges with their axis spacing.
    padded = np.pad(binary, 1)
    top_edges = int(np.count_nonzero(binary & ~padded[:-2, 1:-1]))
    bottom_edges = int(np.count_nonzero(binary & ~padded[2:, 1:-1]))
    left_edges = int(np.count_nonzero(binary & ~padded[1:-1, :-2]))
    right_edges = int(np.count_nonzero(binary & ~padded[1:-1, 2:]))
    boundary_edges = top_edges + bottom_edges + left_edges + right_edges
    boundary_mask = binary & (~padded[:-2, 1:-1] | ~padded[2:, 1:-1]
                              | ~padded[1:-1, :-2] | ~padded[1:-1, 2:])
    mask_pixels = int(binary.sum())
    pixel_area = sy * sx
    total_skeleton_pixels = len(skeleton_points)
    largest_centerline = max(component_skeleton_counts.values(), default=0)
    candidate_rows = []
    for component_id, pixels in enumerate(components, start=1):
        component_points = [point for point in skeleton_points if labels[point] == component_id]
        component_lengths = sum(edge_length(point, neighbor) for point in component_points
                                for neighbor in adjacency[point] if point < neighbor and labels[neighbor] == component_id)
        candidate_rows.append({"candidate_id": component_id, "mask_pixels": len(pixels),
                               "centerline_pixels": len(component_points),
                               "centerline_length": round(component_lengths, 2), "length_unit": unit})
    candidate_rows.sort(key=lambda item: item["mask_pixels"], reverse=True)
    endpoint_count = len(endpoints)
    branch_segments = sum(max(1, sum(degree[point] == 1 for point in group)
                              + sum(degree[point] >= 3 for point in group) - 1)
                          for group in skeleton_components)
    perimeter = (top_edges + bottom_edges) * sx + (left_edges + right_edges) * sy
    quality_flags = []
    if not mask_pixels:
        quality_flags.append({"code": "empty_prediction", "severity": "warning", "message": "No artery pixels were predicted."})
    if len(components) > 1:
        quality_flags.append({"code": "disconnected_regions", "severity": "review", "message": "The predicted mask has disconnected candidate regions; inspect whether branches were lost or separated."})
    if mask_pixels and (binary[0].any() or binary[-1].any() or binary[:, 0].any() or binary[:, -1].any()):
        quality_flags.append({"code": "touches_frame_boundary", "severity": "review", "message": "Predicted artery pixels touch the frame edge and may be clipped."})
    short_paths = [path for path in centerline_paths if path["path_type"] == "centerline" and path["length"] <= 3 * (sx + sy) / 2]
    if short_paths:
        quality_flags.append({"code": "short_paths", "severity": "review", "message": f"{len(short_paths)} short centerline path(s) may be spurs or real small branches; review the image."})
    isolated_paths = sum(path["path_type"] == "isolated" for path in centerline_paths)
    if isolated_paths:
        quality_flags.append({"code": "isolated_skeleton_pixels", "severity": "review", "message": f"{isolated_paths} isolated skeleton pixel(s) were retained for review."})
    uncertainty_fraction = None
    mean_foreground_probability = None
    if probabilities is not None:
        band = np.abs(probabilities - threshold) <= 0.1
        uncertainty_fraction = float(band.mean())
        mean_foreground_probability = float(probabilities[binary].mean()) if binary.any() else None
        if uncertainty_fraction > 0.15:
            quality_flags.append({"code": "uncertain_pixels", "severity": "review", "message": "Many pixels are near the selected segmentation threshold; inspect the probability map."})
        if mean_foreground_probability is not None and mean_foreground_probability < threshold + 0.1:
            quality_flags.append({"code": "low_foreground_score", "severity": "review", "message": "Predicted artery pixels have a low mean uncalibrated score."})
    quality_flags.append({"code": "manual_review_required", "severity": "info", "message": "Centerlines and measurements are algorithmic 2D estimates and require image review."})
    return {
        "mask_pixels": mask_pixels, "centerline_pixels": total_skeleton_pixels,
        "centerline_length": round(centerline_length, 2), "diameter_unit": unit,
        "mean_diameter": round(float(np.mean(diameters)), 2) if diameters else None,
        "minimum_diameter": round(float(np.percentile(diameters, 10)), 2) if diameters else None,
        "maximum_diameter": round(float(np.percentile(diameters, 90)), 2) if diameters else None,
        "diameter_cv": round(float(np.std(diameters) / np.mean(diameters)), 3) if diameters and np.mean(diameters) else None,
        "diameter_samples": len(diameters), "connected_components": len(components),
        "vessel_candidates": candidate_rows[:20], "boundary_pixels": int(boundary_mask.sum()),
        "boundary_length": round(perimeter, 2), "branching_points": junction_count,
        "endpoints": endpoint_count, "branch_segments": branch_segments,
        "branch_points": branch_points, "endpoint_points": endpoint_points,
        "centerline_paths": centerline_paths,
        "quality_status": "review_required" if any(flag["severity"] in {"warning", "review"} for flag in quality_flags) else "information_only",
        "quality_flags": quality_flags, "uncertain_pixel_fraction": round(uncertainty_fraction, 4) if uncertainty_fraction is not None else None,
        "mean_foreground_probability": round(mean_foreground_probability, 4) if mean_foreground_probability is not None else None,
        "continuity_ratio": round(largest_centerline / max(total_skeleton_pixels, 1), 4),
        "tortuosity": round(max_tortuosity, 3) if max_tortuosity is not None else None,
        "projected_mask_area": round(mask_pixels * pixel_area, 2), "area_unit": "mm2" if calibrated else "px2",
        "cross_section_area": None, "cross_section_area_status": "requires_3d_volume",
        "calibration": "source_pixel_spacing" if calibrated else "unavailable",
    }


def build_model():
    import torch
    from torch import nn

    class Block(nn.Module):
        def __init__(self, input_channels: int, output_channels: int):
            super().__init__()
            self.layers = nn.Sequential(
                nn.Conv2d(input_channels, output_channels, 3, padding=1), nn.BatchNorm2d(output_channels), nn.ReLU(inplace=True),
                nn.Conv2d(output_channels, output_channels, 3, padding=1), nn.BatchNorm2d(output_channels), nn.ReLU(inplace=True),
            )

        def forward(self, x):
            return self.layers(x)

    class TinyUNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.down1 = Block(1, 16)
            self.down2 = Block(16, 32)
            self.middle = Block(32, 64)
            self.pool = nn.MaxPool2d(2)
            self.up2 = nn.ConvTranspose2d(64, 32, 2, stride=2)
            self.decode2 = Block(64, 32)
            self.up1 = nn.ConvTranspose2d(32, 16, 2, stride=2)
            self.decode1 = Block(32, 16)
            self.output = nn.Conv2d(16, 1, 1)

        def forward(self, x):
            a = self.down1(x)
            b = self.down2(self.pool(a))
            c = self.middle(self.pool(b))
            d = self.decode2(torch.cat((self.up2(c), b), dim=1))
            return self.output(self.decode1(torch.cat((self.up1(d), a), dim=1)))

    return TinyUNet()


def build_attention_unet():
    """A compact Attention U-Net used as the advanced ARCADE comparator."""
    import torch
    from torch import nn

    class ConvBlock(nn.Module):
        def __init__(self, in_channels: int, out_channels: int):
            super().__init__()
            self.layers = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 3, padding=1, bias=False),
                nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
                nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True),
            )

        def forward(self, value):
            return self.layers(value)

    class AttentionGate(nn.Module):
        def __init__(self, gate_channels: int, skip_channels: int, hidden_channels: int):
            super().__init__()
            self.gate = nn.Conv2d(gate_channels, hidden_channels, 1, bias=False)
            self.skip = nn.Conv2d(skip_channels, hidden_channels, 1, bias=False)
            self.score = nn.Sequential(nn.ReLU(inplace=True), nn.Conv2d(hidden_channels, 1, 1), nn.Sigmoid())

        def forward(self, gate, skip):
            weight = self.score(self.gate(gate) + self.skip(skip))
            self.last_attention_map = weight.detach()
            return skip * weight

    class AttentionUNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.pool = nn.MaxPool2d(2)
            self.enc1 = ConvBlock(1, 16)
            self.enc2 = ConvBlock(16, 32)
            self.bridge = ConvBlock(32, 64)
            self.up2 = nn.ConvTranspose2d(64, 32, 2, stride=2)
            self.att2 = AttentionGate(32, 32, 16)
            self.dec2 = ConvBlock(64, 32)
            self.up1 = nn.ConvTranspose2d(32, 16, 2, stride=2)
            self.att1 = AttentionGate(16, 16, 8)
            self.dec1 = ConvBlock(32, 16)
            self.output = nn.Conv2d(16, 1, 1)

        def forward(self, value):
            first = self.enc1(value)
            second = self.enc2(self.pool(first))
            bridge = self.bridge(self.pool(second))
            up_second = self.up2(bridge)
            decoded_second = self.dec2(torch.cat((up_second, self.att2(up_second, second)), dim=1))
            up_first = self.up1(decoded_second)
            decoded_first = self.dec1(torch.cat((up_first, self.att1(up_first, first)), dim=1))
            return self.output(decoded_first)

    return AttentionUNet()
