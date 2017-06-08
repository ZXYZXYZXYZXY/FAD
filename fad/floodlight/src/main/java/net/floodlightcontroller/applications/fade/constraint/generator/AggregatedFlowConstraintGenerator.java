package net.floodlightcontroller.applications.fade.constraint.generator;

import com.google.common.collect.Lists;
import net.floodlightcontroller.applications.fade.exception.InvalidArgumentException;
import net.floodlightcontroller.applications.fade.flow.Flow;
import net.floodlightcontroller.applications.fade.flow.FlowNode;
import net.floodlightcontroller.applications.fade.flow.aggregatedflow.AggregatedFlow;
import net.floodlightcontroller.applications.fade.rule.generator.RuleGenerateResult;
import net.floodlightcontroller.applications.fade.rule.manager.DedicatedRuleManager;
import net.floodlightcontroller.applications.fade.rule.manager.RuleIndexer;

import java.util.Collection;
import java.util.Collections;
import java.util.List;

/**
 * constraint generator for {@link AggregatedFlow}
 *
 * @implNote In contrast to generateConstraint in SingleFlowConstraintGenerator, the suspicious flows are different,
 *            the validation of flow is different, and the releasing of stats is different.
 */
public class AggregatedFlowConstraintGenerator extends SingleFlowConstraintGenerator {

    private static final int SLICE_RATIO = 2;

    public AggregatedFlowConstraintGenerator(DedicatedRuleManager dedicatedRuleManager, RuleIndexer ruleIndexer, double acceptedDeviation, boolean ignoreTimeoutIssues) {
        super(dedicatedRuleManager, ruleIndexer, acceptedDeviation, ignoreTimeoutIssues);
    }

    @Override
    protected void validateFlows(Flow flow) {
        if(!(flow instanceof AggregatedFlow)) {
            throw new InvalidArgumentException("This class only generate constraints for AggregatedFlow.");
        }
    }

    @Override
    protected Collection<Flow> generateSuspiciousFlows(Flow flow, FlowNode pos1, FlowNode pos2) {
        AggregatedFlow af = (AggregatedFlow) flow;
        AggregatedFlow split = af.split(pos1, pos2);
        List<AggregatedFlow> slice = split.slice(split.size() / SLICE_RATIO);
        List<Flow> result = Lists.newArrayListWithCapacity(slice.size());
        for(AggregatedFlow tmp : slice){
            if(tmp.length() != 0 && tmp.size() != 0){
                result.add(tmp);
            }
        }
        return result;
    }
}
