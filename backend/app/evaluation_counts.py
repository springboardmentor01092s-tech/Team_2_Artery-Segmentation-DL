"""Supplemental metrics from saved counts only; no image/model processing.

These summaries never replace a frozen evaluator or its macro aggregation.
"""


def _counts(value, names):
    if not isinstance(value, dict) or set(value) != set(names):
        raise ValueError('Exact count fields required')
    if any(type(value[name]) is not int or value[name] < 0 for name in names):
        raise ValueError('Nonnegative integer counts required; booleans are invalid')
    return dict(value)


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def binary_count_summary(counts, *, unit):
    if unit not in ('pixel', 'image'):
        raise ValueError('True-negative metrics require a defined pixel or image unit')
    c = _counts(counts, ('tp', 'fp', 'fn', 'tn'))
    tp, fp, fn, tn = (c[name] for name in ('tp', 'fp', 'fn', 'tn'))
    return dict(schema_version='corovision.saved-count-summary.v1', unit=unit,
                aggregation='micro_from_supplied_counts', counts=c,
                accuracy=_ratio(tp+tn, tp+fp+fn+tn), precision=_ratio(tp, tp+fp),
                recall=_ratio(tp, tp+fn), sensitivity=_ratio(tp, tp+fn),
                specificity=_ratio(tn, tn+fp), false_positive_rate=_ratio(fp, fp+tn),
                false_negative_rate=_ratio(fn, fn+tp), f1=_ratio(2*tp, 2*tp+fp+fn),
                dice=_ratio(2*tp, 2*tp+fp+fn) if unit == 'pixel' else None,
                iou=_ratio(tp, tp+fp+fn) if unit == 'pixel' else None,
                notes=['Undefined denominators remain null, never silently zero or one.',
                       'Micro count summaries do not replace means of per-case metrics.',
                       'Source counts are not independently recounted from pixels here.'])


def lesion_count_summary(counts, *, images):
    c = _counts(counts, ('tp', 'fp', 'fn'))
    if type(images) is not int or images <= 0:
        raise ValueError('Positive integer evaluated-image support required')
    tp, fp, fn = (c[name] for name in ('tp', 'fp', 'fn'))
    return dict(schema_version='corovision.saved-count-summary.v1', unit='matched_lesion',
                aggregation='micro_from_supplied_counts', counts=c, evaluated_images=images,
                precision=_ratio(tp, tp+fp), recall=_ratio(tp, tp+fn),
                sensitivity=_ratio(tp, tp+fn), f1=_ratio(2*tp, 2*tp+fp+fn),
                false_negative_rate=_ratio(fn, fn+tp), false_positives_per_image=fp/images,
                tn=None, accuracy=None, specificity=None, false_positive_rate=None,
                unavailable_reason='No defined lesion-level true-negative population; FP per image is not FPR.',
                notes=['Preserve the source mask/box matching rule and operating threshold.',
                       'No mAP, AUC, clinical validity or patient independence follows from these counts.'])
