'use client'

import { useMemo } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

interface PortfolioPieProps {
  data: { name: string; value: number; color: string }[]
}

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4']

export function PortfolioPie({ data }: PortfolioPieProps) {
  const chartData = useMemo(() => {
    return data.map((item, index) => ({
      ...item,
      color: item.color || COLORS[index % COLORS.length],
    }))
  }, [data])

  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#12121A',
              border: '1px solid #2A2A3A',
              borderRadius: '8px',
              color: '#FFFFFF',
              fontSize: '12px',
            }}
            formatter={(value: number) => [`$${value.toLocaleString()}`, 'Value']}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => <span className="text-sm text-[#9CA3AF]">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
