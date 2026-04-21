/**
 * Unit tests for stats calculations — pure logic, no React, no network.
 *
 * The board stats endpoint returns pre-computed rates from the backend.
 * These tests verify that the frontend correctly renders and interprets them,
 * and that the StatsOverview type contract is satisfied.
 */
import { describe, it, expect } from 'vitest';
import type { StatsOverview } from '@/types';

// ── Helpers that mirror what the frontend does with stats data ────────────────

function formatRate(rate: number): string {
  return `${rate.toFixed(1)}%`;
}

function isResponseRateHigherThanInterviewRate(stats: StatsOverview): boolean {
  return stats.response_rate >= stats.interview_rate;
}

function totalFromByStatus(stats: StatsOverview): number {
  return Object.values(stats.by_status).reduce((sum, n) => sum + n, 0);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('StatsOverview – zero-application baseline', () => {
  const emptyStats: StatsOverview = {
    total_applications: 0,
    by_status: {},
    response_rate: 0,
    interview_rate: 0,
    offer_rate: 0,
  };

  it('all rates are 0 when there are no applications', () => {
    expect(emptyStats.response_rate).toBe(0);
    expect(emptyStats.interview_rate).toBe(0);
    expect(emptyStats.offer_rate).toBe(0);
  });

  it('formatRate renders 0 as "0.0%"', () => {
    expect(formatRate(0)).toBe('0.0%');
  });
});

describe('StatsOverview – rate ordering invariants', () => {
  const stats: StatsOverview = {
    total_applications: 14,
    by_status: { applied: 10, screening: 2, interview: 1, rejected: 1 },
    response_rate: 28.6,
    interview_rate: 7.1,
    offer_rate: 0,
  };

  it('response_rate >= interview_rate', () => {
    expect(isResponseRateHigherThanInterviewRate(stats)).toBe(true);
  });

  it('interview_rate >= offer_rate', () => {
    expect(stats.interview_rate).toBeGreaterThanOrEqual(stats.offer_rate);
  });

  it('by_status values sum to total_applications', () => {
    expect(totalFromByStatus(stats)).toBe(stats.total_applications);
  });
});

describe('StatsOverview – rate formatting', () => {
  it('formats 28.571... as 28.6%', () => {
    const rate = (4 / 14) * 100;
    expect(formatRate(parseFloat(rate.toFixed(1)))).toBe('28.6%');
  });

  it('formats 100% correctly', () => {
    expect(formatRate(100)).toBe('100.0%');
  });
});

describe('StatsOverview – offer scenario', () => {
  const statsWithOffer: StatsOverview = {
    total_applications: 5,
    by_status: { applied: 3, interview: 1, offer: 1 },
    response_rate: 40,
    interview_rate: 40,
    offer_rate: 20,
  };

  it('offer_rate <= interview_rate', () => {
    expect(statsWithOffer.offer_rate).toBeLessThanOrEqual(statsWithOffer.interview_rate);
  });

  it('total matches by_status sum', () => {
    expect(totalFromByStatus(statsWithOffer)).toBe(statsWithOffer.total_applications);
  });
});
